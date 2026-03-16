"""
HR and Payroll models for Saudi Arabia.
Complete module: GOSI, Saudization, EOSB, Payroll, Leave, Attendance, WPS, Documents.
"""
from decimal import Decimal
from datetime import date
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Saudi GOSI contribution rates
GOSI_SAUDI_EMPLOYER_RATE = Decimal("0.10")
GOSI_SAUDI_EMPLOYEE_RATE = Decimal("0.10")
GOSI_EXPAT_EMPLOYER_RATE = Decimal("0.02")
GOSI_EXPAT_EMPLOYEE_RATE = Decimal("0.00")


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
        EXPAT = "expat", "وافد"

    class EmploymentStatus(models.TextChoices):
        ACTIVE = "active", "نشط"
        TERMINATED = "terminated", "منتهي"
        ON_LEAVE = "on_leave", "في إجازة"

    # Identity
    employee_number = models.CharField(max_length=20, unique=True)
    name_ar = models.CharField("الاسم (عربي)", max_length=255)
    name_en = models.CharField("Name (English)", max_length=255)
    national_id = models.CharField("رقم الهوية / الإقامة", max_length=20, blank=True)
    iqama_number = models.CharField("رقم الإقامة", max_length=20, blank=True)
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

    # Banking (WPS)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_code = models.CharField("رمز البنك (SWIFT)", max_length=20, blank=True)
    iban = models.CharField("رقم IBAN", max_length=34, blank=True)

    # Contract
    contract_type = models.CharField(max_length=20, choices=[
        ("permanent", "دائم — Permanent"),
        ("fixed", "محدد المدة — Fixed Term"),
        ("probation", "تجربة — Probation"),
    ], default="permanent")
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True)
    probation_end = models.DateField(null=True, blank=True)

    # Leave balances
    annual_leave_balance = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal("21.0"))
    sick_leave_balance = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal("30.0"))

    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "موظف"
        verbose_name_plural = "الموظفون"

    def __str__(self):
        return f"{self.employee_number} — {self.name_ar}"

    @property
    def gross_salary(self):
        return self.basic_salary + self.housing_allowance + self.transport_allowance + self.other_allowances

    @property
    def is_saudi(self):
        return self.nationality == self.Nationality.SAUDI

    @property
    def years_of_service(self):
        end = self.termination_date or date.today()
        return round((end - self.hire_date).days / 365.25, 2)

    def calculate_gosi(self) -> dict:
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
        years = Decimal(str(self.years_of_service))
        if years < 2:
            return Decimal("0")
        elif years <= 5:
            return self.basic_salary * years * Decimal("1") / Decimal("3")
        else:
            first_5 = self.basic_salary * Decimal("5") * Decimal("1") / Decimal("3")
            remaining = self.basic_salary * (years - Decimal("5"))
            return first_5 + remaining


class LeaveType(models.Model):
    """Saudi Labour Law leave types."""
    name_ar = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    default_days = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=True)

    class Meta:
        verbose_name = "نوع الإجازة"

    def __str__(self):
        return self.name_ar


class LeaveRequest(models.Model):
    """Employee leave request — approval workflow."""
    class Status(models.TextChoices):
        PENDING = "pending", "معلقة"
        APPROVED = "approved", "معتمدة"
        REJECTED = "rejected", "مرفوضة"
        CANCELLED = "cancelled", "ملغية"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=5, decimal_places=1)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "طلب إجازة"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.name_ar} — {self.leave_type.name_ar} ({self.days} days)"


class Attendance(models.Model):
    """Daily attendance tracking."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=[
        ("present", "حاضر — Present"),
        ("absent", "غائب — Absent"),
        ("late", "متأخر — Late"),
        ("half_day", "نصف يوم — Half Day"),
        ("leave", "إجازة — Leave"),
        ("holiday", "عطلة — Holiday"),
    ], default="present")
    hours_worked = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "حضور"
        unique_together = [("employee", "date")]
        ordering = ["-date"]


class PayrollRun(models.Model):
    """Monthly payroll run — calculate → approve → pay → post to GL."""
    class Status(models.TextChoices):
        DRAFT = "draft", "مسودة"
        CALCULATED = "calculated", "محسوب"
        APPROVED = "approved", "معتمد"
        PAID = "paid", "مدفوع"

    period_month = models.PositiveSmallIntegerField()
    period_year = models.PositiveIntegerField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)

    total_gross = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_gosi_employer = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_gosi_employee = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    employee_count = models.PositiveIntegerField(default=0)

    # WPS submission
    wps_submitted = models.BooleanField(default=False)
    wps_submitted_at = models.DateTimeField(null=True, blank=True)
    wps_reference = models.CharField(max_length=100, blank=True)
    wps_file_generated = models.BooleanField(default=False)

    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="approved_payrolls")
    paid_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="payroll_runs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("period_month", "period_year")]
        verbose_name = "مسير الرواتب"

    def __str__(self):
        return f"Payroll {self.period_year}/{self.period_month:02d}"


class PayrollLine(models.Model):
    """Individual employee's payroll for a given month."""
    payroll = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="lines")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)

    # Earnings
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    housing_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)

    # Deductions
    gosi_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gosi_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    absence_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Net
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)

    # WPS fields
    bank_name = models.CharField(max_length=100, blank=True)
    iban = models.CharField(max_length=34, blank=True)

    class Meta:
        verbose_name = "سطر مسير الرواتب"
        unique_together = [("payroll", "employee")]

    def __str__(self):
        return f"{self.employee.name_ar} — {self.net_salary} SAR"


class TerminationSettlement(models.Model):
    """EOSB settlement on employee termination."""
    class Reason(models.TextChoices):
        RESIGNATION = "resignation", "استقالة — Resignation"
        TERMINATION = "termination", "إنهاء خدمات — Termination"
        CONTRACT_END = "contract_end", "انتهاء العقد — Contract End"
        RETIREMENT = "retirement", "تقاعد — Retirement"

    employee = models.OneToOneField(Employee, on_delete=models.PROTECT, related_name="settlement")
    termination_date = models.DateField()
    reason = models.CharField(max_length=20, choices=Reason.choices)
    years_of_service = models.DecimalField(max_digits=6, decimal_places=2)

    # EOSB calculation
    eosb_amount = models.DecimalField(max_digits=12, decimal_places=2)
    leave_balance_payout = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_dues = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_settlement = models.DecimalField(max_digits=12, decimal_places=2)

    # Status
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تسوية نهاية الخدمة"


class EmployeeDocument(models.Model):
    """Employee documents — contracts, IDs, certificates."""
    class DocType(models.TextChoices):
        CONTRACT = "contract", "عقد عمل — Employment Contract"
        NATIONAL_ID = "national_id", "هوية وطنية / إقامة"
        PASSPORT = "passport", "جواز سفر"
        CERTIFICATE = "certificate", "شهادة"
        GOSI_CERT = "gosi_cert", "شهادة GOSI"
        MEDICAL = "medical", "تقرير طبي"
        OTHER = "other", "أخرى"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    title = models.CharField(max_length=200)
    file_name = models.CharField(max_length=255, blank=True)
    file_data = models.TextField(blank=True, help_text="Base64 encoded file content")
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مستند الموظف"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.employee.name_ar} — {self.title}"


class SaudizationReport(models.Model):
    report_date = models.DateField()
    total_employees = models.PositiveIntegerField()
    saudi_employees = models.PositiveIntegerField()
    saudization_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    nitaqat_band = models.CharField(max_length=20, choices=[
        ("platinum", "بلاتيني — Platinum"),
        ("high_green", "أخضر مرتفع — High Green"),
        ("medium_green", "أخضر متوسط — Medium Green"),
        ("low_green", "أخضر منخفض — Low Green"),
        ("yellow", "أصفر — Yellow"),
        ("red", "أحمر — Red"),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تقرير السعودة"
