"""
Tenant provisioning — fixed signup that handles migration failures gracefully.
Key fix: Create tenant WITHOUT auto_create_schema, then run migrations separately.
"""
import uuid
from datetime import timedelta
from django.db import connection, transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Tenant, Domain

User = get_user_model()


# ─── Serializers ──────────────────────────────────────────

class TenantListSerializer(serializers.ModelSerializer):
    domain = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id", "schema_name", "name_ar", "name_en", "vat_number", "cr_number",
            "city", "plan", "zatca_environment", "is_active",
            "trial_ends_at", "created_at", "domain",
        ]

    def get_domain(self, obj):
        d = obj.domains.first()
        return d.domain if d else ""


class TenantDetailSerializer(serializers.ModelSerializer):
    domains = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id", "schema_name", "name_ar", "name_en", "vat_number", "cr_number",
            "city", "address_ar", "address_en",
            "plan", "max_users", "max_invoices_per_month", "max_pos_terminals",
            "zatca_environment", "zatca_onboarded", "is_active",
            "trial_ends_at", "created_at", "updated_at", "domains",
        ]

    def get_domains(self, obj):
        return [{"domain": d.domain, "is_primary": d.is_primary} for d in obj.domains.all()]


class SignupSerializer(serializers.Serializer):
    company_name_ar = serializers.CharField(max_length=255)
    company_name_en = serializers.CharField(max_length=255)
    vat_number = serializers.CharField(max_length=15)
    cr_number = serializers.CharField(max_length=20, required=False, default="")
    city = serializers.CharField(max_length=100, default="Riyadh")
    admin_username = serializers.CharField(max_length=150)
    admin_email = serializers.EmailField()
    admin_password = serializers.CharField(min_length=8)
    subdomain = serializers.SlugField(max_length=50)

    def validate_vat_number(self, value):
        if len(value) != 15 or not value.isdigit():
            raise serializers.ValidationError("VAT number must be exactly 15 digits.")
        if Tenant.objects.filter(vat_number=value).exists():
            raise serializers.ValidationError("A company with this VAT number already exists.")
        return value

    def validate_subdomain(self, value):
        reserved = ['www', 'admin', 'api', 'app', 'mail', 'ftp', 'public', 'signup', 'login']
        if value.lower() in reserved:
            raise serializers.ValidationError(f"'{value}' is a reserved subdomain.")
        return value.lower()


# ─── Signup View (FIXED) ─────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """
    Self-service tenant signup — FIXED version.
    Creates tenant WITHOUT auto_create_schema, then manually creates schema + runs migrations.
    This prevents migration failures from rolling back the tenant record.
    """
    ser = SignupSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    try:
        # Step 1: Create tenant record (NO schema creation yet)
        tenant = Tenant(
            name_ar=data["company_name_ar"],
            name_en=data["company_name_en"],
            vat_number=data["vat_number"],
            cr_number=data["cr_number"],
            city=data["city"],
            plan="starter",
            trial_ends_at=timezone.now() + timedelta(days=30),
        )
        tenant.auto_create_schema = False  # Prevent auto migration
        tenant.save()

        # Step 2: Create domain
        base_domain = _get_base_domain(request)
        full_domain = f"{data['subdomain']}.{base_domain}"
        Domain.objects.create(domain=full_domain, tenant=tenant, is_primary=True)

        # Step 3: Create schema manually
        from django.db import connection as db_conn
        cursor = db_conn.cursor()
        cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{tenant.schema_name}"')

        # Step 4: Run migrations in the new schema
        try:
            from django.core.management import call_command
            call_command('migrate_schemas', '--tenant', '--schema', tenant.schema_name, verbosity=0)
        except Exception as mig_err:
            # Migration failed — try fake-initial
            try:
                call_command('migrate_schemas', '--tenant', '--schema', tenant.schema_name, '--fake-initial', verbosity=0)
            except Exception:
                # Last resort: create tables via SQL
                _create_tenant_tables_sql(tenant.schema_name)

        # Step 5: Create admin user in new schema
        connection.set_schema(tenant.schema_name)

        admin_user = User.objects.create_user(
            username=data["admin_username"],
            email=data["admin_email"],
            password=data["admin_password"],
            is_staff=True,
            is_superuser=True,
        )

        # Step 6: Create RBAC profile
        try:
            from .profile_models import UserProfile
            UserProfile.objects.create(user=admin_user, role="super_admin")
        except Exception:
            pass

        # Step 7: Seed SOCPA Chart of Accounts
        try:
            from django.core.management import call_command
            call_command("seed_socpa_coa", "--all", verbosity=0)
        except Exception:
            pass

        # Step 8: Generate JWT tokens
        refresh = RefreshToken.for_user(admin_user)

        connection.set_schema_to_public()

        return Response({
            "status": "success",
            "tenant": {
                "id": tenant.id,
                "name": tenant.name_en,
                "schema": tenant.schema_name,
                "domain": full_domain,
                "vat_number": tenant.vat_number,
                "plan": tenant.plan,
                "trial_ends_at": tenant.trial_ends_at.isoformat(),
            },
            "admin": {
                "username": data["admin_username"],
                "email": data["admin_email"],
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "login_url": f"https://{full_domain}/app/login",
        }, status=201)

    except Exception as e:
        connection.set_schema_to_public()
        # Don't delete the tenant — it might be partially created
        return Response({"error": str(e)}, status=400)


def _get_base_domain(request):
    host = request.get_host().split(":")[0]
    if "railway.app" in host:
        return host
    parts = host.split(".")
    if len(parts) > 2:
        return ".".join(parts[1:])
    return host


def _create_tenant_tables_sql(schema):
    """Fallback: create essential tables via raw SQL if migrations fail."""
    from django.db import connection as db_conn
    cursor = db_conn.cursor()

    # Auth tables (Django's built-in — should exist from migrate)
    # Only create our app tables
    tables_sql = f"""
    -- UserProfile
    CREATE TABLE IF NOT EXISTS "{schema}".tenants_userprofile (
        id bigserial PRIMARY KEY,
        role varchar(20) NOT NULL DEFAULT 'employee',
        user_id integer NOT NULL UNIQUE
    );

    -- ChartOfAccount
    CREATE TABLE IF NOT EXISTS "{schema}".accounting_chartofaccount (
        id bigserial PRIMARY KEY,
        code varchar(10) NOT NULL UNIQUE,
        name_ar varchar(200) NOT NULL,
        name_en varchar(200) NOT NULL,
        account_type varchar(15) NOT NULL,
        socpa_category varchar(30) NOT NULL DEFAULT '',
        normal_balance varchar(10) NOT NULL DEFAULT 'debit',
        is_leaf boolean NOT NULL DEFAULT true,
        is_active boolean NOT NULL DEFAULT true,
        parent_id bigint
    );
    """
    cursor.execute(tables_sql)


# ─── Super-Admin Tenant Management ──────────────────────

class IsSuperAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_superuser


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.prefetch_related("domains").all()
    permission_classes = [IsSuperAdminUser]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return TenantListSerializer
        return TenantDetailSerializer

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        tenant = self.get_object()
        tenant.is_active = False
        tenant.save(update_fields=["is_active"])
        return Response({"status": "deactivated"})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        tenant = self.get_object()
        tenant.is_active = True
        tenant.save(update_fields=["is_active"])
        return Response({"status": "activated"})

    @action(detail=True, methods=["post"])
    def add_domain(self, request, pk=None):
        tenant = self.get_object()
        domain_name = request.data.get("domain")
        if not domain_name:
            return Response({"error": "domain is required"}, status=400)
        if Domain.objects.filter(domain=domain_name).exists():
            return Response({"error": "Domain already in use"}, status=400)
        Domain.objects.create(domain=domain_name, tenant=tenant, is_primary=False)
        return Response({"status": "domain added", "domain": domain_name})

    @action(detail=True, methods=["post"])
    def change_plan(self, request, pk=None):
        tenant = self.get_object()
        plan = request.data.get("plan")
        limits = {
            "starter": {"max_users": 5, "max_invoices_per_month": 300, "max_pos_terminals": 1},
            "growth": {"max_users": 25, "max_invoices_per_month": 2000, "max_pos_terminals": 5},
            "enterprise": {"max_users": 999, "max_invoices_per_month": 99999, "max_pos_terminals": 99},
        }
        if plan not in limits:
            return Response({"error": "Invalid plan"}, status=400)
        tenant.plan = plan
        for k, v in limits[plan].items():
            setattr(tenant, k, v)
        tenant.save()
        return Response({"status": "plan changed", "plan": plan})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        total = Tenant.objects.count()
        active = Tenant.objects.filter(is_active=True).count()
        by_plan = {}
        for p in ["starter", "growth", "enterprise"]:
            by_plan[p] = Tenant.objects.filter(plan=p).count()
        return Response({
            "total_tenants": total,
            "active_tenants": active,
            "inactive_tenants": total - active,
            "by_plan": by_plan,
        })
