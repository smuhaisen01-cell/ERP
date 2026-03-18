"""
Tenant provisioning — public schema API for:
1. Self-service signup (creates tenant + admin user + seeds data)
2. Super-admin tenant management (list/update/deactivate tenants)

All endpoints under /api/public/tenants/ — run on public schema.
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
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id", "schema_name", "name_ar", "name_en", "vat_number", "cr_number",
            "city", "plan", "zatca_environment", "is_active",
            "trial_ends_at", "created_at", "domain", "user_count",
        ]

    def get_domain(self, obj):
        d = obj.domains.first()
        return d.domain if d else ""

    def get_user_count(self, obj):
        try:
            connection.set_schema(obj.schema_name)
            count = User.objects.count()
            connection.set_schema_to_public()
            return count
        except Exception:
            connection.set_schema_to_public()
            return 0


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
    """Self-service tenant signup."""
    # Company info
    company_name_ar = serializers.CharField(max_length=255)
    company_name_en = serializers.CharField(max_length=255)
    vat_number = serializers.CharField(max_length=15)
    cr_number = serializers.CharField(max_length=20, required=False, default="")
    city = serializers.CharField(max_length=100, default="Riyadh")

    # Admin user
    admin_username = serializers.CharField(max_length=150)
    admin_email = serializers.EmailField()
    admin_password = serializers.CharField(min_length=8)

    # Subdomain (e.g., "acme" → acme.erp.sa)
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
        if Domain.objects.filter(domain__startswith=f"{value}.").exists():
            raise serializers.ValidationError(f"Subdomain '{value}' is already taken.")
        return value.lower()

    def validate_admin_username(self, value):
        # We'll check inside the tenant schema during creation
        return value


# ─── Signup View ──────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """
    Self-service tenant signup.
    Creates: Tenant → Domain → Schema → Admin user → Seeds SOCPA CoA
    Returns JWT tokens for immediate login.
    """
    ser = SignupSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    try:
        with transaction.atomic():
            # 1. Create tenant (auto_create_schema=True)
            tenant = Tenant.objects.create(
                name_ar=data["company_name_ar"],
                name_en=data["company_name_en"],
                vat_number=data["vat_number"],
                cr_number=data["cr_number"],
                city=data["city"],
                plan="starter",
                trial_ends_at=timezone.now() + timedelta(days=30),
            )

            # 2. Create domain record
            # Build full domain from subdomain + base domain
            base_domain = _get_base_domain(request)
            full_domain = f"{data['subdomain']}.{base_domain}"

            Domain.objects.create(
                domain=full_domain,
                tenant=tenant,
                is_primary=True,
            )

            # 3. Create admin user in the new tenant schema
            connection.set_schema(tenant.schema_name)

            admin_user = User.objects.create_user(
                username=data["admin_username"],
                email=data["admin_email"],
                password=data["admin_password"],
                is_staff=True,
                is_superuser=True,
            )

            # 4. Create RBAC profile
            try:
                from .profile_models import UserProfile
                UserProfile.objects.create(user=admin_user, role="super_admin")
            except Exception:
                pass

            # 5. Seed SOCPA Chart of Accounts
            try:
                from django.core.management import call_command
                call_command("seed_socpa_coa", "--all", verbosity=0)
            except Exception:
                pass

            # 6. Generate JWT tokens
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
        return Response({"error": str(e)}, status=400)


def _get_base_domain(request):
    """Extract base domain from current request host.
    erp-production-7d8b.up.railway.app → erp-production-7d8b.up.railway.app
    erp.sa → erp.sa
    company1.erp.sa → erp.sa
    """
    host = request.get_host().split(":")[0]
    # If it's a Railway URL, use the full hostname
    if "railway.app" in host:
        return host
    # Otherwise, strip first subdomain to get base
    parts = host.split(".")
    if len(parts) > 2:
        return ".".join(parts[1:])
    return host


# ─── Super-Admin Tenant Management ──────────────────────

class IsSuperAdminUser(IsAuthenticated):
    """Only public-schema superusers."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_superuser


class TenantViewSet(viewsets.ModelViewSet):
    """
    Super-admin tenant management.
    List, create, update, deactivate tenants.
    """
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
        """Add a custom domain to a tenant."""
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
        """Change tenant's plan."""
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
        """Dashboard stats for super-admin."""
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
