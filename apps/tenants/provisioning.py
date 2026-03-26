"""
Tenant provisioning — BULLETPROOF version.
Key design: NO transaction.atomic() wrapping the whole flow.
Each step is independent so tenant record persists even if migration fails.
"""
import logging
from datetime import timedelta
from django.db import connection
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Tenant, Domain

User = get_user_model()
logger = logging.getLogger("apps.tenants")


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
    cr_number = serializers.CharField(max_length=20, required=False, default="", allow_blank=True)
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
        if Domain.objects.filter(domain__startswith=f"{value}.").exists():
            raise serializers.ValidationError(f"Subdomain '{value}' is already taken.")
        return value.lower()


# ─── Signup View ──────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """
    Self-service tenant signup — BULLETPROOF version.
    NO transaction.atomic() so tenant record persists even if migration fails.
    """
    ser = SignupSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    tenant = None
    full_domain = ""
    try:
        # ── Step 1: Create tenant record (NO auto_create_schema) ──
        tenant = Tenant(
            name_ar=data["company_name_ar"],
            name_en=data["company_name_en"],
            vat_number=data["vat_number"],
            cr_number=data["cr_number"],
            city=data["city"],
            plan="starter",
            trial_ends_at=timezone.now() + timedelta(days=30),
        )
        tenant.auto_create_schema = False
        tenant.save()
        logger.info(f"[SIGNUP] Tenant created: {tenant.schema_name} (id={tenant.id})")

        # ── Step 2: Create domain ──
        base_domain = _get_base_domain(request)
        full_domain = f"{data['subdomain']}.{base_domain}"
        Domain.objects.create(domain=full_domain, tenant=tenant, is_primary=True)
        logger.info(f"[SIGNUP] Domain created: {full_domain}")

        # ── Step 3: Create schema ──
        cursor = connection.cursor()
        cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{tenant.schema_name}"')
        logger.info(f"[SIGNUP] Schema created: {tenant.schema_name}")

        # ── Step 4: Create tables via SQL (most reliable) ──
        _create_tenant_tables_sql(tenant.schema_name)
        logger.info(f"[SIGNUP] Tables created in {tenant.schema_name}")

        # ── Step 5: Create admin user ──
        connection.set_schema(tenant.schema_name)

        admin_user = User.objects.create_user(
            username=data["admin_username"],
            email=data["admin_email"],
            password=data["admin_password"],
            is_staff=True,
            is_superuser=True,
        )
        logger.info(f"[SIGNUP] Admin user created: {data['admin_username']}")

        # ── Step 6: Create RBAC profile ──
        try:
            from .profile_models import UserProfile
            UserProfile.objects.create(user=admin_user, role="super_admin")
        except Exception as e:
            logger.warning(f"[SIGNUP] Profile creation skipped: {e}")

        # ── Step 7: Seed SOCPA Chart of Accounts ──
        try:
            from django.core.management import call_command
            call_command("seed_socpa_coa", "--all", verbosity=0)
            logger.info(f"[SIGNUP] SOCPA CoA seeded")
        except Exception as e:
            logger.warning(f"[SIGNUP] CoA seeding skipped: {e}")

        # ── Step 8: Fake migrations so future migrate_schemas --tenant skips ──
        try:
            _fake_tenant_migrations(tenant.schema_name)
        except Exception:
            pass

        # ── Step 9: Generate JWT tokens ──
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
        logger.error(f"[SIGNUP] Failed: {e}")
        # Don't delete tenant — it was saved. Admin can fix manually.
        return Response({
            "error": str(e),
            "tenant_created": tenant.id if tenant and tenant.pk else False,
        }, status=400)


def _get_base_domain(request):
    host = request.get_host().split(":")[0]
    if "railway.app" in host:
        return host
    parts = host.split(".")
    if len(parts) > 2:
        return ".".join(parts[1:])
    return host


def _fake_tenant_migrations(schema_name):
    """Insert migration records so future migrate_schemas --tenant skips this schema."""
    cursor = connection.cursor()
    apps_to_fake = [
        ('contenttypes', '0001_initial'), ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0001_initial'), ('auth', '0002_alter_permission_name_max_length'),
        ('auth', '0003_alter_user_email_max_length'), ('auth', '0004_alter_user_username_opts'),
        ('auth', '0005_alter_user_last_login_null'), ('auth', '0006_require_contenttypes_0002'),
        ('auth', '0007_alter_validators_add_error_messages'), ('auth', '0008_alter_user_username_max_length'),
        ('auth', '0009_alter_user_last_name_max_length'), ('auth', '0010_alter_group_name_max_length'),
        ('auth', '0011_update_proxy_permissions'), ('auth', '0012_alter_user_first_name_max_length'),
        ('admin', '0001_initial'), ('admin', '0002_logentry_remove_auto_add'), ('admin', '0003_logentry_add_action_flag_choices'),
        ('sessions', '0001_initial'),
        ('accounting', '0001_initial'), ('zatca', '0001_initial'), ('hr', '0001_initial'),
        ('pos', '0001_initial'), ('inventory', '0001_initial'), ('tenants', '0001_initial'),
        ('sales', '0001_initial'), ('ai', '0001_initial'), ('billing', '0001_initial'),
    ]
    for app, name in apps_to_fake:
        cursor.execute(
            f'INSERT INTO "{schema_name}".django_migrations (app, name, applied) VALUES (%s, %s, NOW()) ON CONFLICT DO NOTHING',
            [app, name]
        )


def _create_tenant_tables_sql(schema):
    """Create ALL tenant tables directly via SQL — bypasses Django migrations entirely."""
    cursor = connection.cursor()
    s = schema

    sqls = [
        # Django core tables
        f'''CREATE TABLE IF NOT EXISTS "{s}".django_migrations (
            id serial PRIMARY KEY, app varchar(255) NOT NULL,
            name varchar(255) NOT NULL, applied timestamp with time zone NOT NULL DEFAULT now()
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".django_content_type (
            id serial PRIMARY KEY, app_label varchar(100) NOT NULL,
            model varchar(100) NOT NULL, UNIQUE(app_label, model)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".auth_permission (
            id serial PRIMARY KEY, name varchar(255) NOT NULL,
            content_type_id integer REFERENCES "{s}".django_content_type(id),
            codename varchar(100) NOT NULL, UNIQUE(content_type_id, codename)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".auth_group (
            id serial PRIMARY KEY, name varchar(150) NOT NULL UNIQUE
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".auth_group_permissions (
            id bigserial PRIMARY KEY, group_id integer REFERENCES "{s}".auth_group(id),
            permission_id integer REFERENCES "{s}".auth_permission(id),
            UNIQUE(group_id, permission_id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".auth_user (
            id serial PRIMARY KEY, password varchar(128) NOT NULL,
            last_login timestamp with time zone, is_superuser boolean NOT NULL DEFAULT false,
            username varchar(150) NOT NULL UNIQUE, first_name varchar(150) NOT NULL DEFAULT '',
            last_name varchar(150) NOT NULL DEFAULT '', email varchar(254) NOT NULL DEFAULT '',
            is_staff boolean NOT NULL DEFAULT false, is_active boolean NOT NULL DEFAULT true,
            date_joined timestamp with time zone NOT NULL DEFAULT now()
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".auth_user_groups (
            id bigserial PRIMARY KEY, user_id integer REFERENCES "{s}".auth_user(id),
            group_id integer REFERENCES "{s}".auth_group(id), UNIQUE(user_id, group_id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".auth_user_user_permissions (
            id bigserial PRIMARY KEY, user_id integer REFERENCES "{s}".auth_user(id),
            permission_id integer REFERENCES "{s}".auth_permission(id), UNIQUE(user_id, permission_id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".django_admin_log (
            id serial PRIMARY KEY, action_time timestamp with time zone NOT NULL DEFAULT now(),
            object_id text, object_repr varchar(200) NOT NULL, action_flag smallint NOT NULL,
            change_message text NOT NULL DEFAULT '',
            content_type_id integer REFERENCES "{s}".django_content_type(id),
            user_id integer NOT NULL REFERENCES "{s}".auth_user(id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".django_session (
            session_key varchar(40) PRIMARY KEY, session_data text NOT NULL,
            expire_date timestamp with time zone NOT NULL
        )''',

        # RBAC
        f'''CREATE TABLE IF NOT EXISTS "{s}".tenants_userprofile (
            id bigserial PRIMARY KEY, role varchar(20) NOT NULL DEFAULT 'employee',
            user_id integer NOT NULL UNIQUE REFERENCES "{s}".auth_user(id) ON DELETE CASCADE
        )''',

        # Accounting
        f'''CREATE TABLE IF NOT EXISTS "{s}".accounting_chartofaccount (
            id bigserial PRIMARY KEY, code varchar(10) NOT NULL UNIQUE,
            name_ar varchar(200) NOT NULL, name_en varchar(200) NOT NULL,
            account_type varchar(15) NOT NULL, socpa_category varchar(30) NOT NULL DEFAULT '',
            normal_balance varchar(10) NOT NULL DEFAULT 'debit',
            is_leaf boolean NOT NULL DEFAULT true, is_active boolean NOT NULL DEFAULT true,
            parent_id bigint REFERENCES "{s}".accounting_chartofaccount(id) ON DELETE SET NULL
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".accounting_journalentry (
            id bigserial PRIMARY KEY, entry_number varchar(50) NOT NULL UNIQUE,
            entry_date date NOT NULL, description_ar text NOT NULL DEFAULT '',
            description_en text NOT NULL DEFAULT '', reference varchar(100) NOT NULL DEFAULT '',
            status varchar(15) NOT NULL DEFAULT 'draft',
            created_at timestamp with time zone NOT NULL DEFAULT now(),
            posted_at timestamp with time zone,
            created_by_id integer NOT NULL REFERENCES "{s}".auth_user(id),
            posted_by_id integer REFERENCES "{s}".auth_user(id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".accounting_journalentryline (
            id bigserial PRIMARY KEY, description_ar varchar(255) NOT NULL DEFAULT '',
            debit_amount decimal(18,2) NOT NULL DEFAULT 0, credit_amount decimal(18,2) NOT NULL DEFAULT 0,
            account_id bigint NOT NULL REFERENCES "{s}".accounting_chartofaccount(id),
            entry_id bigint NOT NULL REFERENCES "{s}".accounting_journalentry(id) ON DELETE CASCADE
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".accounting_vatreturn (
            id bigserial PRIMARY KEY, period_start date NOT NULL, period_end date NOT NULL,
            status varchar(15) NOT NULL DEFAULT 'draft',
            total_sales decimal(18,2) NOT NULL DEFAULT 0, total_vat decimal(18,2) NOT NULL DEFAULT 0,
            created_at timestamp with time zone NOT NULL DEFAULT now()
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".accounting_zakatreturn (
            id bigserial PRIMARY KEY, fiscal_year integer NOT NULL,
            status varchar(15) NOT NULL DEFAULT 'draft',
            zakatable_amount decimal(18,2) NOT NULL DEFAULT 0, zakat_due decimal(18,2) NOT NULL DEFAULT 0,
            created_at timestamp with time zone NOT NULL DEFAULT now()
        )''',

        # ZATCA
        f'''CREATE TABLE IF NOT EXISTS "{s}".zatca_taxinvoice (
            id bigserial PRIMARY KEY, uuid uuid NOT NULL UNIQUE,
            invoice_number varchar(50) NOT NULL UNIQUE, invoice_type varchar(3) NOT NULL,
            invoice_type_code varchar(10) NOT NULL DEFAULT '0100000',
            issue_date date NOT NULL, issue_time time NOT NULL,
            hijri_date varchar(20) NOT NULL DEFAULT '',
            buyer_name_ar varchar(255) NOT NULL DEFAULT '', buyer_vat_number varchar(15) NOT NULL DEFAULT '',
            buyer_cr_number varchar(20) NOT NULL DEFAULT '', buyer_address text NOT NULL DEFAULT '',
            subtotal decimal(18,2) NOT NULL, discount_total decimal(18,2) NOT NULL DEFAULT 0,
            taxable_amount decimal(18,2) NOT NULL, vat_amount decimal(18,2) NOT NULL,
            total_amount decimal(18,2) NOT NULL,
            invoice_hash varchar(64) NOT NULL DEFAULT '', previous_hash varchar(64) NOT NULL DEFAULT '',
            digital_signature text NOT NULL DEFAULT '', qr_code_tlv text NOT NULL DEFAULT '',
            signed_xml text NOT NULL DEFAULT '',
            zatca_status varchar(15) NOT NULL DEFAULT 'pending',
            zatca_response_code varchar(10) NOT NULL DEFAULT '',
            zatca_response_message text NOT NULL DEFAULT '',
            zatca_cleared_at timestamp with time zone,
            zatca_submission_attempts smallint NOT NULL DEFAULT 0, zatca_uuid uuid,
            is_cancelled boolean NOT NULL DEFAULT false,
            created_by_id integer NOT NULL REFERENCES "{s}".auth_user(id),
            created_at timestamp with time zone NOT NULL DEFAULT now()
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".zatca_taxinvoiceline (
            id bigserial PRIMARY KEY, line_number smallint NOT NULL,
            description_ar varchar(500) NOT NULL, description_en varchar(500) NOT NULL DEFAULT '',
            quantity decimal(12,4) NOT NULL, unit varchar(20) NOT NULL DEFAULT 'EA',
            unit_price decimal(18,4) NOT NULL, discount_amount decimal(18,2) NOT NULL DEFAULT 0,
            line_total decimal(18,2) NOT NULL, vat_rate decimal(5,2) NOT NULL DEFAULT 15,
            vat_amount decimal(18,2) NOT NULL, vat_category_code varchar(5) NOT NULL DEFAULT 'S',
            invoice_id bigint NOT NULL REFERENCES "{s}".zatca_taxinvoice(id) ON DELETE CASCADE
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".zatca_zatcainvoicelog (
            id bigserial PRIMARY KEY, invoice_hash varchar(64) NOT NULL,
            action varchar(20) NOT NULL, status_code varchar(10) NOT NULL DEFAULT '',
            response_body text NOT NULL DEFAULT '',
            created_at timestamp with time zone NOT NULL DEFAULT now(),
            invoice_id bigint NOT NULL REFERENCES "{s}".zatca_taxinvoice(id) ON DELETE CASCADE
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".zatca_tenantzatcacredential (
            id bigserial PRIMARY KEY, terminal_id varchar(50) NOT NULL,
            csid text NOT NULL DEFAULT '', private_key_encrypted text NOT NULL DEFAULT '',
            csid_expires_at timestamp with time zone, is_active boolean NOT NULL DEFAULT true,
            created_at timestamp with time zone NOT NULL DEFAULT now()
        )''',

        # HR
        f'''CREATE TABLE IF NOT EXISTS "{s}".hr_department (
            id bigserial PRIMARY KEY, name_ar varchar(100) NOT NULL,
            name_en varchar(100) NOT NULL, cost_center varchar(20) NOT NULL DEFAULT '',
            manager_id bigint
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".hr_employee (
            id bigserial PRIMARY KEY, employee_number varchar(20) NOT NULL UNIQUE,
            name_ar varchar(255) NOT NULL, name_en varchar(255) NOT NULL,
            national_id varchar(20) NOT NULL DEFAULT '', iqama_number varchar(20) NOT NULL DEFAULT '',
            passport_number varchar(30) NOT NULL DEFAULT '', gosi_number varchar(20) NOT NULL DEFAULT '',
            nationality varchar(10) NOT NULL, job_title_ar varchar(200) NOT NULL,
            job_title_en varchar(200) NOT NULL DEFAULT '',
            hire_date date NOT NULL, termination_date date,
            status varchar(15) NOT NULL DEFAULT 'active',
            basic_salary decimal(12,2) NOT NULL, housing_allowance decimal(12,2) NOT NULL DEFAULT 0,
            transport_allowance decimal(12,2) NOT NULL DEFAULT 0, other_allowances decimal(12,2) NOT NULL DEFAULT 0,
            bank_name varchar(100) NOT NULL DEFAULT '', bank_code varchar(20) NOT NULL DEFAULT '',
            iban varchar(34) NOT NULL DEFAULT '',
            contract_type varchar(20) NOT NULL DEFAULT 'permanent',
            contract_start date, contract_end date, probation_end date,
            annual_leave_balance decimal(5,1) NOT NULL DEFAULT 21.0,
            sick_leave_balance decimal(5,1) NOT NULL DEFAULT 30.0,
            department_id bigint NOT NULL REFERENCES "{s}".hr_department(id),
            user_id integer UNIQUE REFERENCES "{s}".auth_user(id),
            created_at timestamp with time zone NOT NULL DEFAULT now(),
            updated_at timestamp with time zone NOT NULL DEFAULT now()
        )''',
        f'ALTER TABLE "{s}".hr_department ADD FOREIGN KEY (manager_id) REFERENCES "{s}".hr_employee(id) ON DELETE SET NULL NOT VALID',
        f'''CREATE TABLE IF NOT EXISTS "{s}".hr_leavetype (
            id bigserial PRIMARY KEY, name_ar varchar(100) NOT NULL, name_en varchar(100) NOT NULL,
            code varchar(20) NOT NULL UNIQUE, default_days integer NOT NULL DEFAULT 0, is_paid boolean NOT NULL DEFAULT true
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".hr_leaverequest (
            id bigserial PRIMARY KEY, start_date date NOT NULL, end_date date NOT NULL,
            days decimal(5,1) NOT NULL, reason text NOT NULL DEFAULT '',
            status varchar(15) NOT NULL DEFAULT 'pending', rejection_reason text NOT NULL DEFAULT '',
            approved_at timestamp with time zone, created_at timestamp with time zone NOT NULL DEFAULT now(),
            employee_id bigint NOT NULL REFERENCES "{s}".hr_employee(id),
            leave_type_id bigint NOT NULL REFERENCES "{s}".hr_leavetype(id),
            approved_by_id integer REFERENCES "{s}".auth_user(id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".hr_attendance (
            id bigserial PRIMARY KEY, date date NOT NULL,
            check_in time, check_out time, status varchar(15) NOT NULL DEFAULT 'present',
            hours_worked decimal(4,2) NOT NULL DEFAULT 0, overtime_hours decimal(4,2) NOT NULL DEFAULT 0,
            notes text NOT NULL DEFAULT '',
            employee_id bigint NOT NULL REFERENCES "{s}".hr_employee(id),
            UNIQUE(employee_id, date)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".hr_payrollrun (
            id bigserial PRIMARY KEY, period_month smallint NOT NULL, period_year integer NOT NULL,
            status varchar(15) NOT NULL DEFAULT 'draft',
            total_gross decimal(18,2) NOT NULL DEFAULT 0, total_deductions decimal(18,2) NOT NULL DEFAULT 0,
            total_gosi_employer decimal(18,2) NOT NULL DEFAULT 0, total_gosi_employee decimal(18,2) NOT NULL DEFAULT 0,
            total_net decimal(18,2) NOT NULL DEFAULT 0, employee_count integer NOT NULL DEFAULT 0,
            wps_submitted boolean NOT NULL DEFAULT false, wps_submitted_at timestamp with time zone,
            wps_reference varchar(100) NOT NULL DEFAULT '', wps_file_generated boolean NOT NULL DEFAULT false,
            paid_at timestamp with time zone,
            created_at timestamp with time zone NOT NULL DEFAULT now(),
            approved_by_id integer REFERENCES "{s}".auth_user(id),
            created_by_id integer NOT NULL REFERENCES "{s}".auth_user(id),
            UNIQUE(period_month, period_year)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".hr_payrollline (
            id bigserial PRIMARY KEY,
            basic_salary decimal(12,2) NOT NULL, housing_allowance decimal(12,2) NOT NULL DEFAULT 0,
            transport_allowance decimal(12,2) NOT NULL DEFAULT 0, other_allowances decimal(12,2) NOT NULL DEFAULT 0,
            overtime_pay decimal(12,2) NOT NULL DEFAULT 0, gross_salary decimal(12,2) NOT NULL,
            gosi_employee decimal(12,2) NOT NULL DEFAULT 0, gosi_employer decimal(12,2) NOT NULL DEFAULT 0,
            absence_deduction decimal(12,2) NOT NULL DEFAULT 0, loan_deduction decimal(12,2) NOT NULL DEFAULT 0,
            other_deductions decimal(12,2) NOT NULL DEFAULT 0, total_deductions decimal(12,2) NOT NULL DEFAULT 0,
            net_salary decimal(12,2) NOT NULL,
            bank_name varchar(100) NOT NULL DEFAULT '', iban varchar(34) NOT NULL DEFAULT '',
            employee_id bigint NOT NULL REFERENCES "{s}".hr_employee(id),
            payroll_id bigint NOT NULL REFERENCES "{s}".hr_payrollrun(id) ON DELETE CASCADE,
            UNIQUE(payroll_id, employee_id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".hr_terminationsettlement (
            id bigserial PRIMARY KEY, termination_date date NOT NULL,
            reason varchar(20) NOT NULL, years_of_service decimal(6,2) NOT NULL,
            eosb_amount decimal(12,2) NOT NULL, leave_balance_payout decimal(12,2) NOT NULL DEFAULT 0,
            other_dues decimal(12,2) NOT NULL DEFAULT 0, deductions decimal(12,2) NOT NULL DEFAULT 0,
            total_settlement decimal(12,2) NOT NULL,
            is_paid boolean NOT NULL DEFAULT false, paid_at timestamp with time zone,
            notes text NOT NULL DEFAULT '', created_at timestamp with time zone NOT NULL DEFAULT now(),
            employee_id bigint NOT NULL UNIQUE REFERENCES "{s}".hr_employee(id),
            created_by_id integer NOT NULL REFERENCES "{s}".auth_user(id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".hr_employeedocument (
            id bigserial PRIMARY KEY, doc_type varchar(20) NOT NULL,
            title varchar(200) NOT NULL, file_name varchar(255) NOT NULL DEFAULT '',
            file_data text NOT NULL DEFAULT '',
            issue_date date, expiry_date date, notes text NOT NULL DEFAULT '',
            uploaded_at timestamp with time zone NOT NULL DEFAULT now(),
            employee_id bigint NOT NULL REFERENCES "{s}".hr_employee(id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".hr_saudizationreport (
            id bigserial PRIMARY KEY, report_date date NOT NULL,
            total_employees integer NOT NULL, saudi_employees integer NOT NULL,
            saudization_percentage decimal(5,2) NOT NULL, nitaqat_band varchar(20) NOT NULL,
            created_at timestamp with time zone NOT NULL DEFAULT now()
        )''',

        # POS
        f'''CREATE TABLE IF NOT EXISTS "{s}".pos_branch (
            id bigserial PRIMARY KEY, code varchar(10) NOT NULL UNIQUE,
            name_ar varchar(100) NOT NULL, name_en varchar(100) NOT NULL,
            city varchar(50) NOT NULL DEFAULT 'Riyadh', address_ar text NOT NULL DEFAULT '',
            is_active boolean NOT NULL DEFAULT true
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".pos_posterminal (
            id bigserial PRIMARY KEY, terminal_id varchar(20) NOT NULL UNIQUE,
            name varchar(100) NOT NULL, is_active boolean NOT NULL DEFAULT true,
            zatca_csid_registered boolean NOT NULL DEFAULT false,
            zatca_registered_at timestamp with time zone,
            branch_id bigint NOT NULL REFERENCES "{s}".pos_branch(id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".pos_possession (
            id bigserial PRIMARY KEY, opened_at timestamp with time zone NOT NULL,
            closed_at timestamp with time zone, status varchar(10) NOT NULL DEFAULT 'open',
            opening_cash decimal(12,2) NOT NULL, closing_cash decimal(12,2),
            total_sales decimal(18,2) NOT NULL DEFAULT 0, total_vat decimal(18,2) NOT NULL DEFAULT 0,
            total_cash decimal(18,2) NOT NULL DEFAULT 0, total_mada decimal(18,2) NOT NULL DEFAULT 0,
            total_stc_pay decimal(18,2) NOT NULL DEFAULT 0, total_credit_card decimal(18,2) NOT NULL DEFAULT 0,
            transaction_count integer NOT NULL DEFAULT 0,
            cashier_id integer NOT NULL REFERENCES "{s}".auth_user(id),
            terminal_id bigint NOT NULL REFERENCES "{s}".pos_posterminal(id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".pos_postransaction (
            id bigserial PRIMARY KEY, transaction_number varchar(50) NOT NULL UNIQUE,
            payment_method varchar(20) NOT NULL DEFAULT 'cash',
            subtotal decimal(18,2) NOT NULL, discount decimal(18,2) NOT NULL DEFAULT 0,
            vat_amount decimal(18,2) NOT NULL, total_amount decimal(18,2) NOT NULL,
            amount_paid decimal(18,2) NOT NULL DEFAULT 0, change_due decimal(18,2) NOT NULL DEFAULT 0,
            transacted_at timestamp with time zone NOT NULL,
            session_id bigint NOT NULL REFERENCES "{s}".pos_possession(id),
            zatca_invoice_id bigint REFERENCES "{s}".zatca_taxinvoice(id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".pos_postransactionline (
            id bigserial PRIMARY KEY, product_code varchar(50) NOT NULL DEFAULT '',
            product_name_ar varchar(200) NOT NULL, product_name_en varchar(200) NOT NULL DEFAULT '',
            quantity decimal(12,4) NOT NULL, unit_price decimal(18,4) NOT NULL,
            discount_amount decimal(18,2) NOT NULL DEFAULT 0, vat_rate decimal(5,2) NOT NULL DEFAULT 15,
            vat_amount decimal(18,2) NOT NULL, line_total decimal(18,2) NOT NULL,
            transaction_id bigint NOT NULL REFERENCES "{s}".pos_postransaction(id) ON DELETE CASCADE
        )''',

        # Inventory
        f'''CREATE TABLE IF NOT EXISTS "{s}".inventory_productcategory (
            id bigserial PRIMARY KEY, name_ar varchar(100) NOT NULL, name_en varchar(100) NOT NULL,
            parent_id bigint REFERENCES "{s}".inventory_productcategory(id), is_active boolean NOT NULL DEFAULT true
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".inventory_product (
            id bigserial PRIMARY KEY, sku varchar(50) NOT NULL UNIQUE, barcode varchar(50) NOT NULL DEFAULT '',
            name_ar varchar(255) NOT NULL, name_en varchar(255) NOT NULL,
            description_ar text NOT NULL DEFAULT '', description_en text NOT NULL DEFAULT '',
            category_id bigint REFERENCES "{s}".inventory_productcategory(id),
            product_type varchar(15) NOT NULL DEFAULT 'goods',
            cost_price decimal(12,2) NOT NULL DEFAULT 0, selling_price decimal(12,2) NOT NULL DEFAULT 0,
            vat_inclusive boolean NOT NULL DEFAULT false, unit varchar(20) NOT NULL DEFAULT 'EA',
            is_trackable boolean NOT NULL DEFAULT true,
            reorder_level decimal(12,2) NOT NULL DEFAULT 0, reorder_quantity decimal(12,2) NOT NULL DEFAULT 0,
            min_stock decimal(12,2) NOT NULL DEFAULT 0, max_stock decimal(12,2) NOT NULL DEFAULT 0,
            revenue_account_code varchar(10) NOT NULL DEFAULT '4100',
            cogs_account_code varchar(10) NOT NULL DEFAULT '5100',
            inventory_account_code varchar(10) NOT NULL DEFAULT '1140',
            is_active boolean NOT NULL DEFAULT true,
            created_at timestamp with time zone NOT NULL DEFAULT now(),
            updated_at timestamp with time zone NOT NULL DEFAULT now()
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".inventory_warehouse (
            id bigserial PRIMARY KEY, code varchar(20) NOT NULL UNIQUE,
            name_ar varchar(100) NOT NULL, name_en varchar(100) NOT NULL,
            city varchar(50) NOT NULL DEFAULT 'Riyadh', address text NOT NULL DEFAULT '',
            is_active boolean NOT NULL DEFAULT true, is_default boolean NOT NULL DEFAULT false
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".inventory_stocklevel (
            id bigserial PRIMARY KEY, quantity decimal(12,2) NOT NULL DEFAULT 0,
            reserved decimal(12,2) NOT NULL DEFAULT 0, last_counted_at timestamp with time zone,
            product_id bigint NOT NULL REFERENCES "{s}".inventory_product(id) ON DELETE CASCADE,
            warehouse_id bigint NOT NULL REFERENCES "{s}".inventory_warehouse(id) ON DELETE CASCADE,
            UNIQUE(product_id, warehouse_id)
        )''',
        f'''CREATE TABLE IF NOT EXISTS "{s}".inventory_stockmovement (
            id bigserial PRIMARY KEY, movement_number varchar(50) NOT NULL UNIQUE,
            movement_type varchar(15) NOT NULL, quantity decimal(12,2) NOT NULL,
            unit_cost decimal(12,2) NOT NULL DEFAULT 0, total_cost decimal(18,2) NOT NULL DEFAULT 0,
            reference varchar(100) NOT NULL DEFAULT '', notes text NOT NULL DEFAULT '',
            created_at timestamp with time zone NOT NULL DEFAULT now(),
            product_id bigint NOT NULL REFERENCES "{s}".inventory_product(id),
            warehouse_id bigint NOT NULL REFERENCES "{s}".inventory_warehouse(id),
            to_warehouse_id bigint REFERENCES "{s}".inventory_warehouse(id),
            created_by_id integer NOT NULL REFERENCES "{s}".auth_user(id)
        )''',
    ]

    for sql in sqls:
        try:
            cursor.execute(sql)
        except Exception as e:
            logger.warning(f"[SQL] Skipped (may already exist): {e}")
            connection.cursor()  # Reset cursor after error


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
            return Response({"error": "domain required"}, status=400)
        if Domain.objects.filter(domain=domain_name).exists():
            return Response({"error": "Domain in use"}, status=400)
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
            "total_tenants": total, "active_tenants": active,
            "inactive_tenants": total - active, "by_plan": by_plan,
        })
