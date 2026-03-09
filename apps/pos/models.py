"""
Point of Sale (POS) models — offline-first.
Each terminal is a separate ZATCA EGS unit (separate CSID).
B2C invoices issued immediately; ZATCA reporting async within 24h.
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Branch(models.Model):
    code = models.CharField("رمز الفرع", max_length=10, unique=True)  # e.g. RUH, JED
    name_ar = models.CharField("اسم الفرع (عربي)", max_length=100)
    name_en = models.CharField("Branch Name", max_length=100, blank=True)
    city = models.CharField("المدينة", max_length=50)
    address_ar = models.TextField("العنوان (عربي)")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "فرع"

    def __str__(self):
        return f"{self.code} — {self.name_ar}"


class POSTerminal(models.Model):
    """Each terminal needs its own ZATCA CSID (separate EGS unit)."""
    terminal_id = models.CharField(max_length=20, unique=True)  # e.g. RUH-T01
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="terminals")
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    # ZATCA credentials managed via TenantZATCACredential (public schema)
    zatca_csid_registered = models.BooleanField(default=False)
    zatca_registered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "طرفية نقطة بيع"

    def __str__(self):
        return f"{self.terminal_id} ({self.branch.name_ar})"


class POSSession(models.Model):
    """A cashier's daily session — opens at start of shift, closes at end."""
    class Status(models.TextChoices):
        OPEN   = "open",   "مفتوح"
        CLOSED = "closed", "مغلق"

    terminal = models.ForeignKey(POSTerminal, on_delete=models.PROTECT)
    cashier = models.ForeignKey(User, on_delete=models.PROTECT)
    opened_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    opening_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Z-Report totals (calculated on close)
    total_sales = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_cash = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_mada = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_stc_pay = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_credit_card = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    transaction_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "جلسة نقطة بيع"

    def __str__(self):
        return f"{self.terminal.terminal_id} — {self.opened_at.date()} ({self.cashier})"


class POSTransaction(models.Model):
    """
    Individual POS sale.
    Receipt printed immediately.
    ZATCA simplified invoice (B2C, type 386) created and queued for reporting.
    """
    class PaymentMethod(models.TextChoices):
        CASH        = "cash",        "نقدي"
        MADA        = "mada",        "مدى"
        STC_PAY     = "stc_pay",     "STC Pay"
        CREDIT_CARD = "credit_card", "بطاقة ائتمان"
        APPLE_PAY   = "apple_pay",   "Apple Pay"

    session = models.ForeignKey(POSSession, on_delete=models.PROTECT, related_name="transactions")
    transaction_number = models.CharField(max_length=50, unique=True)
    payment_method = models.CharField(max_length=15, choices=PaymentMethod.choices)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    change_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transacted_at = models.DateTimeField()

    # ZATCA — simplified invoice reference
    zatca_invoice = models.OneToOneField(
        "zatca.TaxInvoice",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="pos_transaction",
    )

    # Offline sync tracking
    created_offline = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "معاملة نقطة بيع"
        indexes = [
            models.Index(fields=["transacted_at"]),
        ]

    def __str__(self):
        return f"{self.transaction_number} — {self.total_amount} SAR"


class POSTransactionLine(models.Model):
    transaction = models.ForeignKey(POSTransaction, on_delete=models.CASCADE, related_name="lines")
    product_code = models.CharField(max_length=50)
    product_name_ar = models.CharField(max_length=255)
    product_name_en = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
