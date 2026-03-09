"""
Tenant model — the foundation of the multi-tenant architecture.
Each tenant gets its own PostgreSQL schema: t_{vat_number}
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Tenant(TenantMixin):
    """
    One row per customer company.
    schema_name = t_{vat_number} — set automatically on save.
    """

    # ─── Saudi Business Identity ──────────────────────────────────────────
    name_ar = models.CharField("اسم الشركة (عربي)", max_length=255)
    name_en = models.CharField("Company Name (English)", max_length=255)
    vat_number = models.CharField(
        "رقم تسجيل ضريبة القيمة المضافة",
        max_length=15,
        unique=True,
        help_text="15-digit Saudi VAT registration number",
    )
    cr_number = models.CharField(
        "رقم السجل التجاري",
        max_length=20,
        blank=True,
        help_text="Commercial Registration number",
    )
    city = models.CharField("المدينة", max_length=100, default="الرياض")
    address_ar = models.TextField("العنوان (عربي)", blank=True)
    address_en = models.TextField("Address (English)", blank=True)

    # ─── Plan + Billing ───────────────────────────────────────────────────
    class Plan(models.TextChoices):
        STARTER    = "starter",    "Starter — 149 SAR/mo"
        GROWTH     = "growth",     "Growth — 499 SAR/mo"
        ENTERPRISE = "enterprise", "Enterprise — Custom"

    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.STARTER)
    max_users = models.PositiveIntegerField(default=5)
    max_invoices_per_month = models.PositiveIntegerField(default=300)
    max_pos_terminals = models.PositiveIntegerField(default=1)

    # ─── ZATCA Configuration ──────────────────────────────────────────────
    class ZATCAEnv(models.TextChoices):
        SANDBOX    = "sandbox",    "Sandbox (Testing)"
        SIMULATION = "simulation", "Simulation"
        PRODUCTION = "production", "Production"

    zatca_environment = models.CharField(
        max_length=15, choices=ZATCAEnv.choices, default=ZATCAEnv.SANDBOX
    )
    zatca_onboarded = models.BooleanField(default=False)

    # ─── Status ───────────────────────────────────────────────────────────
    is_active = models.BooleanField(default=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # django-tenants requires this
    auto_create_schema = True

    class Meta:
        verbose_name = "مستأجر"
        verbose_name_plural = "المستأجرون"

    def __str__(self):
        return f"{self.name_ar} ({self.vat_number})"

    def save(self, *args, **kwargs):
        # Schema name derived from VAT number — guaranteed unique
        if not self.schema_name:
            self.schema_name = f"t_{self.vat_number}"
        super().save(*args, **kwargs)

    @property
    def stream_key(self):
        """Redis Stream key for this tenant's ERP events."""
        return f"erp_events:{self.schema_name}"

    @property
    def kpi_key(self):
        """Redis key for this tenant's KPI cache."""
        return f"kpi:{self.schema_name}"

    @property
    def alert_key(self):
        """Redis key for this tenant's AI alert list."""
        return f"alerts:{self.schema_name}"


class Domain(DomainMixin):
    """Maps subdomains to tenants: acme.yourdomain.sa → Tenant(acme)."""
    pass
