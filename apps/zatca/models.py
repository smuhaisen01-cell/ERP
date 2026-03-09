"""
ZATCA Phase 2 models.
- TenantZATCACredential: CSID per tenant/terminal (public schema)
- TaxInvoice: Every issued invoice with UBL XML, QR, chain hash (tenant schema)
- ZATCAInvoiceLog: Immutable audit log (public schema, 5-year retention)
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TenantZATCACredential(models.Model):
    """
    Per-tenant (and per-POS-terminal) ZATCA cryptographic credentials.
    Stored in PUBLIC schema — accessible to ZATCA service only.
    Private key encrypted at rest with AES-256 (settings.ZATCA_ENCRYPTION_KEY).
    """

    class CredentialType(models.TextChoices):
        TENANT   = "tenant",   "Tenant (ERP)"
        TERMINAL = "terminal", "POS Terminal"

    # tenant_id references the Tenant.schema_name from public schema
    tenant_schema = models.CharField(max_length=100, db_index=True)
    terminal_id = models.CharField(max_length=50, blank=True)  # e.g. "RUH-T01"
    credential_type = models.CharField(max_length=10, choices=CredentialType.choices)

    # ZATCA credentials
    private_key_encrypted = models.BinaryField()   # AES-256 encrypted EC private key
    binary_security_token = models.TextField()     # Base64 CSID certificate
    secret = models.CharField(max_length=255)      # ZATCA secret for this CSID

    class Environment(models.TextChoices):
        SANDBOX    = "sandbox",    "Sandbox"
        SIMULATION = "simulation", "Simulation"
        PRODUCTION = "production", "Production"

    environment = models.CharField(max_length=15, choices=Environment.choices)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    renewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "zatca"
        verbose_name = "شهادة ZATCA"
        unique_together = [("tenant_schema", "terminal_id", "environment")]

    def __str__(self):
        return f"{self.tenant_schema} / {self.terminal_id or 'main'} [{self.environment}]"


class TaxInvoice(models.Model):
    """
    Every tax invoice issued by the ERP.
    UBL 2.1 XML, ECDSA signature, TLV QR code, ZATCA status.
    Lives in TENANT schema.
    """

    class InvoiceType(models.TextChoices):
        STANDARD   = "388", "فاتورة ضريبية — Standard (B2B)"
        SIMPLIFIED = "386", "فاتورة ضريبية مبسطة — Simplified (B2C)"
        DEBIT_NOTE = "383", "إشعار مدين — Debit Note"
        CREDIT_NOTE= "381", "إشعار دائن — Credit Note"

    class ZATCAStatus(models.TextChoices):
        PENDING   = "pending",   "Pending Submission"
        CLEARED   = "cleared",   "Cleared (B2B)"
        REPORTED  = "reported",  "Reported (B2C)"
        REJECTED  = "rejected",  "Rejected"
        ERROR     = "error",     "Submission Error"

    # ZATCA mandatory fields
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    invoice_type = models.CharField(max_length=3, choices=InvoiceType.choices)
    invoice_type_code = models.CharField(max_length=10, default="0100000")  # ZATCA type code

    # Dates — both Gregorian and Hijri (ZATCA requires both)
    issue_date = models.DateField()
    issue_time = models.TimeField()
    hijri_date = models.CharField(max_length=20)  # e.g. "1446-09-15"

    # Buyer info (B2B requires full buyer details)
    buyer_name_ar = models.CharField(max_length=255, blank=True)
    buyer_vat_number = models.CharField(max_length=15, blank=True)
    buyer_cr_number = models.CharField(max_length=20, blank=True)
    buyer_address = models.TextField(blank=True)

    # Amounts (SAR)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2)
    discount_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=18, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=18, decimal_places=2)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2)

    # ZATCA cryptographic fields
    invoice_hash = models.CharField(max_length=64)      # SHA-256 of UBL XML
    previous_hash = models.CharField(max_length=64)     # Chain to previous invoice
    digital_signature = models.TextField()               # ECDSA signature (base64)
    qr_code_tlv = models.TextField()                     # Base64 TLV QR code
    signed_xml = models.TextField()                      # Complete signed UBL 2.1 XML

    # ZATCA submission
    zatca_status = models.CharField(
        max_length=15, choices=ZATCAStatus.choices, default=ZATCAStatus.PENDING
    )
    zatca_response_code = models.CharField(max_length=10, blank=True)
    zatca_response_message = models.TextField(blank=True)
    zatca_cleared_at = models.DateTimeField(null=True, blank=True)
    zatca_submission_attempts = models.PositiveSmallIntegerField(default=0)
    zatca_uuid = models.UUIDField(null=True, blank=True)  # ZATCA's UUID after clearance

    # Audit
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    is_cancelled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "فاتورة ضريبية"
        verbose_name_plural = "الفواتير الضريبية"
        indexes = [
            models.Index(fields=["zatca_status", "invoice_type"]),
            models.Index(fields=["issue_date"]),
        ]

    def __str__(self):
        return f"{self.invoice_number} ({self.get_invoice_type_display()})"

    @property
    def is_b2b(self):
        return self.invoice_type == self.InvoiceType.STANDARD

    @property
    def is_b2c(self):
        return self.invoice_type == self.InvoiceType.SIMPLIFIED


class TaxInvoiceLine(models.Model):
    invoice = models.ForeignKey(TaxInvoice, on_delete=models.CASCADE, related_name="lines")
    line_number = models.PositiveSmallIntegerField()
    description_ar = models.CharField(max_length=500)
    description_en = models.CharField(max_length=500, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    unit = models.CharField(max_length=20, default="EA")  # UBL unit code
    unit_price = models.DecimalField(max_digits=18, decimal_places=4)
    discount_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=18, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    vat_amount = models.DecimalField(max_digits=18, decimal_places=2)
    vat_category_code = models.CharField(max_length=5, default="S")  # S=Standard, Z=Zero, E=Exempt

    class Meta:
        ordering = ["line_number"]


class ZATCAInvoiceLog(models.Model):
    """
    IMMUTABLE audit log for all ZATCA submissions.
    Stored in PUBLIC schema — survives tenant deletion.
    5-year retention required by Saudi law.
    AI Platform can READ this log (via ai_readonly role).
    AI Platform can NEVER modify this log.
    """
    tenant_schema = models.CharField(max_length=100, db_index=True)
    invoice_uuid = models.UUIDField(db_index=True)
    invoice_number = models.CharField(max_length=50)
    invoice_type = models.CharField(max_length=3)
    invoice_hash = models.CharField(max_length=64)
    previous_hash = models.CharField(max_length=64)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=18, decimal_places=2)
    zatca_status = models.CharField(max_length=15)
    zatca_response_code = models.CharField(max_length=10, blank=True)
    environment = models.CharField(max_length=15)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "zatca"
        verbose_name = "سجل ZATCA"
        # Immutability enforced by: no update/delete permissions in app layer
        # and by PostgreSQL RLS policy (INSERT only for erp_readwrite)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("ZATCAInvoiceLog is immutable — cannot update an existing record.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("ZATCAInvoiceLog is immutable — records cannot be deleted.")
