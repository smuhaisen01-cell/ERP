"""
HR and Payroll models for Saudi Arabia.
Handles: GOSI contributions, Saudization (Nitaqat), EOSB,
WPS (Wage Protection System), Saudi labour law.
"""
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Saudi GOSI contribution rates
GOSI_SAUDI_EMPLOYER_RATE = Decimal("0.10")   # 10% employer
GOSI_SAUDI_EMPLOYEE_RATE = Decimal("0.10")   # 10% employee
GOSI_EXPAT_EMPLOYER_RATE = Decimal("0.02")   # 2% employer only (expats)
GOSI_EXPAT_EMPLOYEE_RATE = Decimal("0.00")   # 0% employee (expats)

# EOSB: 1 month per year for first 5 years, 1.5 months thereafter
EOSB_RATE_YEAR_1_5 = Decimal("1.0")          # months per year
EOSB_RATE_AFTER_5 = Decimal("1.5")           # months per year


class Department(models.Model):
    name_ar = models.CharField("اسم القسم (عربي)", max_length=100)
    name_en = models.CharField("Department Name (English)", max_length=100)
    cost_center = models.CharField(max_length=20, blank=True)
    manager = models.ForeignKey("Employee", null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_departments")

    class Meta:
        verbose_name = "قسم"

    def __str__(self):
        return self.name_ar


class Employee(models.Model):
    class Nationality(models.TextChoices):
        SAUDI = "saudi", "سعودي"
        EXPAT  = "expat",  "وافد"

    class EmploymentStatus(models.TextChoices):
        ACTIVE     = "active",     "نشط"
        TERMINATED = "terminated", "منتهي"
        ON_LEAVE   = "on_leave",   "في إجازة"

    # Identity
    employee_number = models.CharField(max_length=20, unique=True)
    name_ar = models.CharField("الاسم (عربي)", max_length=255)
    name_en = models.CharField("Name (English)", max_length=255)
    national_id = models.CharField("رقم الهوية / الإقامة", max_length=20, blank=True)
    iqama_number = models.CharField("رقم الإقامة", max_length=20, blank=True)  # Expats
    passport_number = models.CharField(max_length=30, blank=True)
    gosi_number = models.CharField("رقم التأمينات", max_length=20, blank=True)

    # Employment
    nationality = models.CharField(max_length=10, choices=Nationality.choices)
    job_title_ar = models.CharField(max_length=200)
    job_title_en = models.CharField(max_length=200, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    hire_date = models.DateField("تاريخ التعيين")
    termination_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=EmploymentStatus.choices, default=EmploymentStatus.ACTIVE)

    # Salary
    basic_salary = models.DecimalField("الراتب الأساسي (SAR)", max_digits=12, decimal_places=2)
    housing_allowance = models.DecimalField("بدل السكن", max_digits=12, decimal_places=2, default=0)
    transport_allowance = models.DecimalField("بدل المواصلات", max_digits=12, decimal_places=2, default=0)
    other_allowances = models.DecimalField("بدلات أخرى", max_digits=12, decimal_places=2, default=0)

    # Banking (WPS — Wage Protection System)
    bank_name = models.CharField(max_length=100, blank=True)
    iban = models.CharField("رقم IBAN", max_length=34, blank=True)

    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "موظف"
        verbose_name_plural = "الموظفون"

    def __str__(self):
        return f"{self.employee_number} — {self.name_ar}"

    @property
    def gross_salary(self):
        return (
            self.basic_salary
            + self.housing_allowance
            + self.transport_allowance
            + self.other_allowances
        )

    @property
    def is_saudi(self):
        return self.nationality == self.Nationality.SAUDI

    def calculate_gosi(self) -> dict:
        """Calculate GOSI contributions based on nationality."""
        if self.is_saudi:
            employer = self.basic_salary * GOSI_SAUDI_EMPLOYER_RATE
            employee = self.basic_salary * GOSI_SAUDI_EMPLOYEE_RATE
        else:
            employer = self.basic_salary * GOSI_EXPAT_EMPLOYER_RATE
            employee = Decimal("0")
        return {
            "employer_contribution": employer,
            "employee_deduction": employee,
            "total": employer + employee,
        }

    def calculate_eosb(self) -> Decimal:
        """
        Calculate End of Service Benefit (مكافأة نهاية الخدمة).
        Saudi Labour Law: 1/3 of monthly salary per year for first 5 years,
        full monthly salary per year thereafter.
        """
        from datetime import date
        end_date = self.termination_date or date.today()
        years = (end_date - self.hire_date).days / 365.25

        if years < 2:
            return Decimal("0")  # No EOSB for < 2 years service
        elif years <= 5:
            return self.basic_salary * Decimal(str(round(years, 2))) * Decimal("1/3")
        else:
            first_5 = self.basic_salary * Decimal("5") * Decimal("1/3")
            remaining = self.basic_salary * Decimal(str(round(years - 5, 2)))
            return first_5 + remaining


class PayrollRun(models.Model):
    """Monthly payroll run — creates JournalEntry in accounting on post."""
    class Status(models.TextChoices):
        DRAFT     = "draft",     "مسودة"
        APPROVED  = "approved",  "معتمد"
        PROCESSED = "processed", "معالج"
        PAID      = "paid",      "مدفوع"

    period_month = models.PositiveSmallIntegerField()  # 1–12
    period_year = models.PositiveIntegerField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)

    total_gross = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_gosi_employer = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_gosi_employee = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    # WPS submission
    wps_submitted = models.BooleanField(default=False)
    wps_submitted_at = models.DateTimeField(null=True, blank=True)
    wps_reference = models.CharField(max_length=100, blank=True)

    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="payroll_runs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("period_month", "period_year")]
        verbose_name = "مسير الرواتب"

    def __str__(self):
        return f"Payroll {self.period_year}/{self.period_month:02d}"


class SaudizationReport(models.Model):
    """
    Saudization (Nitaqat) monthly tracking.
    Saudi nationals must meet minimum % thresholds per industry/company size.
    """
    report_date = models.DateField()
    total_employees = models.PositiveIntegerField()
    saudi_employees = models.PositiveIntegerField()
    saudization_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    nitaqat_band = models.CharField(
        max_length=20,
        choices=[
            ("platinum", "بلاتيني — Platinum"),
            ("high_green", "أخضر مرتفع — High Green"),
            ("medium_green", "أخضر متوسط — Medium Green"),
            ("low_green", "أخضر منخفض — Low Green"),
            ("yellow", "أصفر — Yellow"),
            ("red", "أحمر — Red"),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تقرير السعودة"
