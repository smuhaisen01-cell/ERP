"""
HR API viewsets — complete module.
Payroll, Leave, Attendance, WPS, Termination, Documents, Saudization.
"""
import io
import csv
import uuid
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Department, Employee, LeaveType, LeaveRequest, Attendance,
    PayrollRun, PayrollLine, TerminationSettlement, EmployeeDocument,
    SaudizationReport, GOSI_SAUDI_EMPLOYER_RATE, GOSI_SAUDI_EMPLOYEE_RATE,
    GOSI_EXPAT_EMPLOYER_RATE,
)
from .serializers import (
    DepartmentSerializer, EmployeeSerializer, EmployeeListSerializer,
    LeaveTypeSerializer, LeaveRequestSerializer, AttendanceSerializer,
    PayrollRunSerializer, PayrollRunListSerializer, PayrollLineSerializer,
    TerminationSettlementSerializer, EmployeeDocumentSerializer,
    SaudizationReportSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    search_fields = ["name_ar", "name_en", "cost_center"]


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("department").all()
    filterset_fields = ["nationality", "status", "department", "contract_type"]
    search_fields = ["employee_number", "name_ar", "name_en", "national_id"]
    ordering_fields = ["name_ar", "hire_date", "basic_salary"]
    ordering = ["name_ar"]

    def get_serializer_class(self):
        if self.action == "list":
            return EmployeeListSerializer
        return EmployeeSerializer

    def perform_create(self, serializer):
        emp_number = f"EMP-{uuid.uuid4().hex[:6].upper()}"
        serializer.save(employee_number=emp_number)

    @action(detail=True, methods=["get"])
    def gosi(self, request, pk=None):
        return Response(self.get_object().calculate_gosi())

    @action(detail=True, methods=["get"])
    def eosb(self, request, pk=None):
        emp = self.get_object()
        return Response({
            "employee": emp.employee_number,
            "name": emp.name_ar,
            "years_of_service": emp.years_of_service,
            "eosb_amount_sar": str(emp.calculate_eosb()),
        })

    @action(detail=True, methods=["get"])
    def payslips(self, request, pk=None):
        """Get all payroll lines for this employee."""
        emp = self.get_object()
        lines = PayrollLine.objects.filter(employee=emp).select_related("payroll").order_by("-payroll__period_year", "-payroll__period_month")
        data = []
        for line in lines:
            data.append({
                "period": f"{line.payroll.period_year}/{line.payroll.period_month:02d}",
                "status": line.payroll.status,
                **PayrollLineSerializer(line).data,
            })
        return Response(data)

    @action(detail=True, methods=["get"])
    def documents(self, request, pk=None):
        docs = self.get_object().documents.all()
        return Response(EmployeeDocumentSerializer(docs, many=True).data)


# ─── Leave Management ────────────────────────────────────

class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer

    @action(detail=False, methods=["post"])
    def seed_defaults(self, request):
        """Seed Saudi Labour Law leave types."""
        defaults = [
            ("annual", "إجازة سنوية", "Annual Leave", 21, True),
            ("sick_full", "إجازة مرضية (كاملة)", "Sick Leave (Full Pay)", 30, True),
            ("sick_75", "إجازة مرضية (75%)", "Sick Leave (75%)", 60, True),
            ("sick_unpaid", "إجازة مرضية (بدون)", "Sick Leave (Unpaid)", 30, False),
            ("maternity", "إجازة أمومة", "Maternity Leave", 70, True),
            ("paternity", "إجازة أبوة", "Paternity Leave", 3, True),
            ("marriage", "إجازة زواج", "Marriage Leave", 5, True),
            ("bereavement", "إجازة وفاة", "Bereavement Leave", 5, True),
            ("hajj", "إجازة حج", "Hajj Leave", 15, True),
            ("unpaid", "إجازة بدون راتب", "Unpaid Leave", 0, False),
        ]
        created = 0
        for code, name_ar, name_en, days, paid in defaults:
            _, was_created = LeaveType.objects.get_or_create(
                code=code,
                defaults={"name_ar": name_ar, "name_en": name_en, "default_days": days, "is_paid": paid}
            )
            if was_created:
                created += 1
        return Response({"created": created, "total": len(defaults)})


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related("employee", "leave_type").all()
    serializer_class = LeaveRequestSerializer
    filterset_fields = ["employee", "leave_type", "status"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        leave = self.get_object()
        if leave.status != LeaveRequest.Status.PENDING:
            return Response({"error": "Only pending requests can be approved."}, status=400)

        with transaction.atomic():
            leave.status = LeaveRequest.Status.APPROVED
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.save()

            # Deduct from balance
            emp = leave.employee
            if leave.leave_type.code == "annual":
                emp.annual_leave_balance -= leave.days
            elif leave.leave_type.code.startswith("sick"):
                emp.sick_leave_balance -= leave.days
            emp.save()

        return Response(LeaveRequestSerializer(leave).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        leave = self.get_object()
        if leave.status != LeaveRequest.Status.PENDING:
            return Response({"error": "Only pending requests can be rejected."}, status=400)

        leave.status = LeaveRequest.Status.REJECTED
        leave.rejection_reason = request.data.get("reason", "")
        leave.save()
        return Response(LeaveRequestSerializer(leave).data)


# ─── Attendance ──────────────────────────────────────────

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related("employee").all()
    serializer_class = AttendanceSerializer
    filterset_fields = ["employee", "date", "status"]
    ordering = ["-date"]

    @action(detail=False, methods=["post"])
    def bulk_checkin(self, request):
        """Bulk check-in for all active employees today."""
        today = date.today()
        employees = Employee.objects.filter(status="active")
        created = 0
        for emp in employees:
            _, was_created = Attendance.objects.get_or_create(
                employee=emp, date=today,
                defaults={"check_in": timezone.now().time(), "status": "present"}
            )
            if was_created:
                created += 1
        return Response({"date": str(today), "checked_in": created, "total": employees.count()})


# ─── Payroll Processing ──────────────────────────────────

class PayrollRunViewSet(viewsets.ModelViewSet):
    queryset = PayrollRun.objects.all()
    filterset_fields = ["status", "period_year"]
    ordering = ["-period_year", "-period_month"]

    def get_serializer_class(self):
        if self.action == "list":
            return PayrollRunListSerializer
        return PayrollRunSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def calculate(self, request, pk=None):
        """Calculate payroll for all active employees. Draft → Calculated."""
        payroll = self.get_object()
        if payroll.status not in (PayrollRun.Status.DRAFT, PayrollRun.Status.CALCULATED):
            return Response({"error": "Only draft/calculated payrolls can be recalculated."}, status=400)

        employees = Employee.objects.filter(status="active")

        with transaction.atomic():
            # Clear existing lines
            payroll.lines.all().delete()

            total_gross = Decimal("0")
            total_deductions = Decimal("0")
            total_gosi_er = Decimal("0")
            total_gosi_ee = Decimal("0")
            total_net = Decimal("0")

            for emp in employees:
                gosi = emp.calculate_gosi()
                gross = emp.gross_salary
                gosi_ee = gosi["employee_deduction"]
                gosi_er = gosi["employer_contribution"]
                deductions = gosi_ee
                net = gross - deductions

                PayrollLine.objects.create(
                    payroll=payroll,
                    employee=emp,
                    basic_salary=emp.basic_salary,
                    housing_allowance=emp.housing_allowance,
                    transport_allowance=emp.transport_allowance,
                    other_allowances=emp.other_allowances,
                    overtime_pay=0,
                    gross_salary=gross,
                    gosi_employee=gosi_ee,
                    gosi_employer=gosi_er,
                    total_deductions=deductions,
                    net_salary=net,
                    bank_name=emp.bank_name,
                    iban=emp.iban,
                )

                total_gross += gross
                total_deductions += deductions
                total_gosi_er += gosi_er
                total_gosi_ee += gosi_ee
                total_net += net

            payroll.total_gross = total_gross
            payroll.total_deductions = total_deductions
            payroll.total_gosi_employer = total_gosi_er
            payroll.total_gosi_employee = total_gosi_ee
            payroll.total_net = total_net
            payroll.employee_count = employees.count()
            payroll.status = PayrollRun.Status.CALCULATED
            payroll.save()

        return Response(PayrollRunSerializer(payroll).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve payroll. Calculated → Approved."""
        payroll = self.get_object()
        if payroll.status != PayrollRun.Status.CALCULATED:
            return Response({"error": "Only calculated payrolls can be approved."}, status=400)

        payroll.status = PayrollRun.Status.APPROVED
        payroll.approved_by = request.user
        payroll.save()
        return Response(PayrollRunSerializer(payroll).data)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        """Mark payroll as paid + create GL journal entry. Approved → Paid."""
        payroll = self.get_object()
        if payroll.status != PayrollRun.Status.APPROVED:
            return Response({"error": "Only approved payrolls can be paid."}, status=400)

        with transaction.atomic():
            payroll.status = PayrollRun.Status.PAID
            payroll.paid_at = timezone.now()
            payroll.save()

            # Auto-create GL journal entry
            self._create_payroll_gl_entry(payroll)

        return Response(PayrollRunSerializer(payroll).data)

    @action(detail=True, methods=["get"])
    def wps_export(self, request, pk=None):
        """Generate WPS (Wage Protection System) CSV file."""
        payroll = self.get_object()
        if payroll.status not in (PayrollRun.Status.APPROVED, PayrollRun.Status.PAID):
            return Response({"error": "Only approved/paid payrolls can generate WPS."}, status=400)

        output = io.StringIO()
        writer = csv.writer(output)

        # WPS header
        writer.writerow([
            "Employee Number", "Employee Name", "National ID / Iqama",
            "Bank Code", "IBAN", "Basic Salary", "Housing",
            "Transport", "Other Allowances", "Deductions",
            "Net Salary", "Currency",
        ])

        for line in payroll.lines.select_related("employee").all():
            emp = line.employee
            writer.writerow([
                emp.employee_number,
                emp.name_en or emp.name_ar,
                emp.national_id or emp.iqama_number,
                emp.bank_code,
                emp.iban,
                str(line.basic_salary),
                str(line.housing_allowance),
                str(line.transport_allowance),
                str(line.other_allowances),
                str(line.total_deductions),
                str(line.net_salary),
                "SAR",
            ])

        payroll.wps_file_generated = True
        payroll.save(update_fields=["wps_file_generated"])

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="WPS_{payroll.period_year}_{payroll.period_month:02d}.csv"'
        return response

    @action(detail=True, methods=["get"])
    def payslip_data(self, request, pk=None):
        """Return payslip data for all employees in this payroll run (for PDF generation)."""
        payroll = self.get_object()
        lines = payroll.lines.select_related("employee", "employee__department").all()
        data = []
        for line in lines:
            emp = line.employee
            data.append({
                "employee_number": emp.employee_number,
                "name_ar": emp.name_ar,
                "name_en": emp.name_en,
                "department": emp.department.name_ar if emp.department else "",
                "job_title": emp.job_title_ar,
                "nationality": emp.nationality,
                "period": f"{payroll.period_year}/{payroll.period_month:02d}",
                "basic_salary": str(line.basic_salary),
                "housing_allowance": str(line.housing_allowance),
                "transport_allowance": str(line.transport_allowance),
                "other_allowances": str(line.other_allowances),
                "overtime_pay": str(line.overtime_pay),
                "gross_salary": str(line.gross_salary),
                "gosi_employee": str(line.gosi_employee),
                "gosi_employer": str(line.gosi_employer),
                "absence_deduction": str(line.absence_deduction),
                "other_deductions": str(line.other_deductions),
                "total_deductions": str(line.total_deductions),
                "net_salary": str(line.net_salary),
                "bank_name": line.bank_name or emp.bank_name,
                "iban": line.iban or emp.iban,
            })
        return Response({
            "payroll_id": payroll.id,
            "period": f"{payroll.period_year}/{payroll.period_month:02d}",
            "status": payroll.status,
            "employee_count": payroll.employee_count,
            "total_net": str(payroll.total_net),
            "payslips": data,
        })

    def _create_payroll_gl_entry(self, payroll):
        """Auto-create GL journal entry for payroll."""
        try:
            from apps.accounting.models import ChartOfAccount, JournalEntry, JournalEntryLine

            salary_exp = ChartOfAccount.objects.filter(code="6100").first()
            gosi_exp = ChartOfAccount.objects.filter(code="6110").first()
            salary_payable = ChartOfAccount.objects.filter(code="2150").first()
            gosi_payable = ChartOfAccount.objects.filter(code="2140").first()

            if not all([salary_exp, gosi_exp, salary_payable, gosi_payable]):
                return

            entry = JournalEntry.objects.create(
                entry_number=f"JE-PAY-{payroll.period_year}{payroll.period_month:02d}",
                entry_date=date.today(),
                description_ar=f"رواتب {payroll.period_year}/{payroll.period_month:02d}",
                description_en=f"Payroll {payroll.period_year}/{payroll.period_month:02d}",
                reference=f"PAYROLL-{payroll.id}",
                status="posted",
                created_by=payroll.created_by,
                posted_by=payroll.created_by,
                posted_at=timezone.now(),
            )

            # Debit: Salary Expense
            JournalEntryLine.objects.create(
                entry=entry, account=salary_exp,
                description_ar="مصروف رواتب", debit_amount=payroll.total_gross, credit_amount=0,
            )
            # Debit: GOSI Employer Expense
            JournalEntryLine.objects.create(
                entry=entry, account=gosi_exp,
                description_ar="GOSI صاحب العمل", debit_amount=payroll.total_gosi_employer, credit_amount=0,
            )
            # Credit: Salaries Payable (net)
            JournalEntryLine.objects.create(
                entry=entry, account=salary_payable,
                description_ar="رواتب مستحقة", debit_amount=0, credit_amount=payroll.total_net,
            )
            # Credit: GOSI Payable (employer + employee)
            gosi_total = payroll.total_gosi_employer + payroll.total_gosi_employee
            JournalEntryLine.objects.create(
                entry=entry, account=gosi_payable,
                description_ar="GOSI مستحق", debit_amount=0, credit_amount=gosi_total,
            )
        except Exception as e:
            import logging
            logging.getLogger("apps.hr").warning(f"Payroll GL entry failed: {e}")


# ─── Termination & EOSB Settlement ──────────────────────

class TerminationSettlementViewSet(viewsets.ModelViewSet):
    queryset = TerminationSettlement.objects.select_related("employee").all()
    serializer_class = TerminationSettlementSerializer
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["post"])
    def calculate(self, request):
        """Calculate EOSB settlement for an employee."""
        emp_id = request.data.get("employee")
        reason = request.data.get("reason", "resignation")
        term_date_str = request.data.get("termination_date", str(date.today()))

        try:
            emp = Employee.objects.get(pk=emp_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=404)

        from datetime import datetime
        term_date = datetime.strptime(term_date_str, "%Y-%m-%d").date()

        # Calculate
        emp.termination_date = term_date
        years = emp.years_of_service
        eosb = emp.calculate_eosb()

        # Leave balance payout (unused annual leave × daily rate)
        daily_rate = emp.basic_salary / Decimal("30")
        leave_payout = emp.annual_leave_balance * daily_rate

        total = eosb + leave_payout

        return Response({
            "employee": emp.employee_number,
            "name": emp.name_ar,
            "years_of_service": years,
            "reason": reason,
            "termination_date": term_date_str,
            "eosb_amount": str(eosb),
            "leave_balance_days": str(emp.annual_leave_balance),
            "leave_balance_payout": str(leave_payout),
            "total_settlement": str(total),
        })

    @action(detail=False, methods=["post"])
    def process(self, request):
        """Process full termination — create settlement, terminate employee, post GL."""
        emp_id = request.data.get("employee")
        reason = request.data.get("reason", "resignation")
        term_date_str = request.data.get("termination_date", str(date.today()))

        try:
            emp = Employee.objects.get(pk=emp_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=404)

        from datetime import datetime
        term_date = datetime.strptime(term_date_str, "%Y-%m-%d").date()

        with transaction.atomic():
            emp.termination_date = term_date
            years = emp.years_of_service
            eosb = emp.calculate_eosb()
            daily_rate = emp.basic_salary / Decimal("30")
            leave_payout = emp.annual_leave_balance * daily_rate
            total = eosb + leave_payout

            settlement = TerminationSettlement.objects.create(
                employee=emp,
                termination_date=term_date,
                reason=reason,
                years_of_service=Decimal(str(years)),
                eosb_amount=eosb,
                leave_balance_payout=leave_payout,
                total_settlement=total,
                created_by=request.user,
            )

            emp.status = Employee.EmploymentStatus.TERMINATED
            emp.save()

            # GL entry for EOSB
            self._create_eosb_gl_entry(emp, settlement)

        return Response(TerminationSettlementSerializer(settlement).data, status=201)

    def _create_eosb_gl_entry(self, emp, settlement):
        try:
            from apps.accounting.models import ChartOfAccount, JournalEntry, JournalEntryLine

            eosb_liability = ChartOfAccount.objects.filter(code="2220").first()
            cash = ChartOfAccount.objects.filter(code="1112").first()

            if not (eosb_liability and cash):
                return

            entry = JournalEntry.objects.create(
                entry_number=f"JE-EOSB-{emp.employee_number}",
                entry_date=settlement.termination_date,
                description_ar=f"تسوية نهاية خدمة — {emp.name_ar}",
                description_en=f"EOSB Settlement — {emp.name_en}",
                reference=f"EOSB-{settlement.id}",
                status="posted",
                created_by=settlement.created_by,
                posted_by=settlement.created_by,
                posted_at=timezone.now(),
            )

            JournalEntryLine.objects.create(
                entry=entry, account=eosb_liability,
                description_ar=f"EOSB — {emp.name_ar}",
                debit_amount=settlement.total_settlement, credit_amount=0,
            )
            JournalEntryLine.objects.create(
                entry=entry, account=cash,
                description_ar=f"صرف EOSB — {emp.name_ar}",
                debit_amount=0, credit_amount=settlement.total_settlement,
            )
        except Exception:
            pass


# ─── Employee Documents ──────────────────────────────────

class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDocument.objects.select_related("employee").all()
    serializer_class = EmployeeDocumentSerializer
    filterset_fields = ["employee", "doc_type"]
    ordering = ["-uploaded_at"]


# ─── Saudization ─────────────────────────────────────────

class SaudizationReportViewSet(viewsets.ModelViewSet):
    queryset = SaudizationReport.objects.all()
    serializer_class = SaudizationReportSerializer
    ordering = ["-report_date"]

    @action(detail=False, methods=["post"])
    def generate(self, request):
        employees = Employee.objects.filter(status="active")
        total = employees.count()
        saudi = employees.filter(nationality="saudi").count()
        pct = Decimal(str(round(saudi / total * 100, 2))) if total > 0 else Decimal("0")

        if pct >= 80: band = "platinum"
        elif pct >= 60: band = "high_green"
        elif pct >= 40: band = "medium_green"
        elif pct >= 25: band = "low_green"
        elif pct >= 10: band = "yellow"
        else: band = "red"

        report = SaudizationReport.objects.create(
            report_date=date.today(), total_employees=total,
            saudi_employees=saudi, saudization_percentage=pct, nitaqat_band=band,
        )
        return Response(SaudizationReportSerializer(report).data, status=201)
