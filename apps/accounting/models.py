"""
Accounting models — SOCPA Chart of Accounts, General Ledger,
VAT 15%, Zakat 2.5%, AP/AR.
Lives in tenant schema (per-company isolation).
"""
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()


class ChartOfAccount(models.Model):
    """
    SOCPA (Saudi Organization for Certified Public Accountants)
    Chart of Accounts — seeded for each new tenant on creation.
    """

    class AccountType(models.TextChoices):
        ASSET       = "asset",       "أصول — Assets"
        LIABILITY   = "liability",   "خصوم — Liabilities"
        EQUITY      = "equity",      "حقوق ملكية — Equity"
        REVENUE     = "revenue",     "إيرادات — Revenue"
        EXPENSE     = "expense",     "مصروفات — Expenses"

    class SOCPACategory(models.TextChoices):
        CURRENT_ASSETS       = "current_assets",       "الأصول المتداولة"
        NON_CURRENT_ASSETS   = "non_current_assets",   "الأصول غير المتداولة"
        CURRENT_LIABILITIES  = "current_liabilities",  "الخصوم المتداولة"
        LONG_TERM_LIABILITIES= "long_term_liabilities","الخصوم طويلة الأجل"
        EQUITY               = "equity",               "حقوق الملكية"
        REVENUE              = "revenue",              "الإيرادات"
        COGS                 = "cogs",                 "تكلفة المبيعات"
        OPERATING_EXPENSES   = "operating_expenses",   "المصروفات التشغيلية"
        OTHER_EXPENSES       = "other_expenses",       "المصروفات الأخرى"

    code = models.CharField("رمز الحساب", max_length=20, db_index=True)
    name_ar = models.CharField("اسم الحساب (عربي)", max_length=255)
    name_en = models.CharField("Account Name (English)", max_length=255)
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    socpa_category = models.CharField(max_length=40, choices=SOCPACategory.choices)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    is_active = models.BooleanField(default=True)
    is_leaf = models.BooleanField(default=True)  # Can post entries only to leaf accounts
    normal_balance = models.CharField(
        max_length=6, choices=[("debit", "Debit"), ("credit", "Credit")]
    )

    # Special purpose flags for VAT and Zakat
    is_vat_account = models.BooleanField(default=False)
    is_zakat_account = models.BooleanField(default=False)

    class Meta:
        ordering = ["code"]
        unique_together = [("code",)]
        verbose_name = "حساب"
        verbose_name_plural = "الحسابات"

    def __str__(self):
        return f"{self.code} — {self.name_ar}"


class JournalEntry(models.Model):
    """
    General Ledger Journal Entry.
    Written exclusively by ERP Core — AI has READ access only.
    """

    class Status(models.TextChoices):
        DRAFT    = "draft",    "مسودة"
        POSTED   = "posted",   "مرحّل"
        REVERSED = "reversed", "معكوس"

    entry_number = models.CharField(max_length=50, unique=True, db_index=True)
    entry_date = models.DateField("تاريخ القيد")
    description_ar = models.TextField("البيان (عربي)")
    description_en = models.TextField("Description (English)", blank=True)
    reference = models.CharField(max_length=100, blank=True)  # Invoice ref, PO, etc.
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    # Who posted — audit trail
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="journal_entries")
    posted_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.PROTECT, related_name="posted_entries"
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # AI fields — anomaly score from AI Platform (written to ai_results schema, read here)
    ai_anomaly_score = models.FloatField(null=True, blank=True)
    ai_anomaly_flagged = models.BooleanField(default=False)

    class Meta:
        verbose_name = "قيد يومية"
        verbose_name_plural = "قيود اليومية"
        indexes = [
            models.Index(fields=["entry_date", "status"]),
        ]

    def __str__(self):
        return f"{self.entry_number} — {self.entry_date}"

    @property
    def is_balanced(self):
        debits = sum(l.debit_amount for l in self.lines.all())
        credits = sum(l.credit_amount for l in self.lines.all())
        return debits == credits


class JournalEntryLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT)
    description_ar = models.CharField(max_length=255, blank=True)
    debit_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    credit_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    cost_center = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "سطر قيد"
        verbose_name_plural = "سطور القيود"


class VATReturn(models.Model):
    """
    Saudi VAT-103 quarterly return.
    Prepared in ERP Core, submitted by authorized accountant.
    """
    period_start = models.DateField()
    period_end = models.DateField()
    filing_deadline = models.DateField()

    # VAT-103 boxes
    box_1_taxable_sales = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    box_2_vat_on_sales = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    box_3_zero_rated = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    box_4_exempt_sales = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    box_5_taxable_purchases = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    box_6_vat_on_purchases = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    box_7_net_vat_due = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Status(models.TextChoices):
        DRAFT     = "draft",     "مسودة"
        SUBMITTED = "submitted", "مُقدَّم"
        ACCEPTED  = "accepted",  "مقبول"

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    zatca_reference = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("period_start", "period_end")]
        verbose_name = "إقرار ضريبة القيمة المضافة"


class ZakatReturn(models.Model):
    """Annual Zakat filing (2.5% on zakatable business assets)."""
    fiscal_year = models.PositiveIntegerField(unique=True)
    zakatable_assets = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    zakatable_liabilities = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    zakat_base = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    zakat_due = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Status(models.TextChoices):
        CALCULATED = "calculated", "محسوب"
        SUBMITTED  = "submitted",  "مُقدَّم"
        PAID       = "paid",       "مدفوع"

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.CALCULATED)
    filing_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    payment_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "إقرار الزكاة"

    def calculate_zakat_due(self):
        from django.conf import settings
        self.zakat_base = max(self.zakatable_assets - self.zakatable_liabilities, 0)
        self.zakat_due = self.zakat_base * settings.ZAKAT_RATE
        return self.zakat_due
