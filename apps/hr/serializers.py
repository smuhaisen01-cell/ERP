"""
HR serializers — complete module: Employee, Leave, Attendance, Payroll, 
Termination, Documents, Saudization, WPS.
"""
from decimal import Decimal
from rest_framework import serializers
from .models import (
    Department, Employee, LeaveType, LeaveRequest, Attendance,
    PayrollRun, PayrollLine, TerminationSettlement, EmployeeDocument,
    SaudizationReport,
)


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "name_ar", "name_en", "cost_center", "manager", "employee_count"]

    def get_employee_count(self, obj):
        return obj.employee_set.filter(status="active").count()


class EmployeeSerializer(serializers.ModelSerializer):
    gross_salary = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_saudi = serializers.BooleanField(read_only=True)
    years_of_service = serializers.FloatField(read_only=True)
    gosi_breakdown = serializers.SerializerMethodField()
    eosb_amount = serializers.SerializerMethodField()
    department_name = serializers.CharField(source="department.name_ar", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id", "employee_number", "name_ar", "name_en",
            "national_id", "iqama_number", "passport_number", "gosi_number",
            "nationality", "job_title_ar", "job_title_en",
            "department", "department_name",
            "hire_date", "termination_date", "status",
            "basic_salary", "housing_allowance", "transport_allowance", "other_allowances",
            "gross_salary", "is_saudi", "years_of_service",
            "bank_name", "bank_code", "iban", "user",
            "contract_type", "contract_start", "contract_end", "probation_end",
            "annual_leave_balance", "sick_leave_balance",
            "gosi_breakdown", "eosb_amount",
            "created_at",
        ]
        read_only_fields = ["id", "employee_number", "created_at"]

    def get_gosi_breakdown(self, obj):
        return obj.calculate_gosi()

    def get_eosb_amount(self, obj):
        return str(obj.calculate_eosb())


class EmployeeListSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name_ar", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id", "employee_number", "name_ar", "name_en", "nationality",
            "job_title_ar", "department_name", "status", "basic_salary",
            "annual_leave_balance",
        ]


# ─── Leave ────────────────────────────────────────────────

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = "__all__"


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name_ar", read_only=True)
    leave_type_name = serializers.CharField(source="leave_type.name_ar", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            "id", "employee", "employee_name", "leave_type", "leave_type_name",
            "start_date", "end_date", "days", "reason",
            "status", "approved_by", "approved_at", "rejection_reason", "created_at",
        ]
        read_only_fields = ["id", "status", "approved_by", "approved_at", "created_at"]


# ─── Attendance ───────────────────────────────────────────

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name_ar", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id", "employee", "employee_name", "date",
            "check_in", "check_out", "status", "hours_worked",
            "overtime_hours", "notes",
        ]


# ─── Payroll ──────────────────────────────────────────────

class PayrollLineSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name_ar", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)
    employee_iban = serializers.CharField(source="employee.iban", read_only=True)

    class Meta:
        model = PayrollLine
        fields = [
            "id", "employee", "employee_name", "employee_number", "employee_iban",
            "basic_salary", "housing_allowance", "transport_allowance",
            "other_allowances", "overtime_pay", "gross_salary",
            "gosi_employee", "gosi_employer", "absence_deduction",
            "loan_deduction", "other_deductions", "total_deductions",
            "net_salary", "bank_name", "iban",
        ]
        read_only_fields = ["id"]


class PayrollRunSerializer(serializers.ModelSerializer):
    lines = PayrollLineSerializer(many=True, read_only=True)

    class Meta:
        model = PayrollRun
        fields = [
            "id", "period_month", "period_year", "status",
            "total_gross", "total_deductions", "total_gosi_employer",
            "total_gosi_employee", "total_net", "employee_count",
            "wps_submitted", "wps_submitted_at", "wps_reference", "wps_file_generated",
            "approved_by", "paid_at", "created_by", "created_at",
            "lines",
        ]
        read_only_fields = [
            "id", "status", "total_gross", "total_deductions",
            "total_gosi_employer", "total_gosi_employee", "total_net",
            "employee_count", "wps_submitted", "wps_submitted_at",
            "wps_file_generated", "approved_by", "paid_at", "created_by", "created_at",
        ]


class PayrollRunListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = [
            "id", "period_month", "period_year", "status",
            "total_gross", "total_net", "employee_count",
            "wps_submitted", "created_at",
        ]


# ─── Termination ──────────────────────────────────────────

class TerminationSettlementSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name_ar", read_only=True)

    class Meta:
        model = TerminationSettlement
        fields = [
            "id", "employee", "employee_name", "termination_date", "reason",
            "years_of_service", "eosb_amount", "leave_balance_payout",
            "other_dues", "deductions", "total_settlement",
            "is_paid", "paid_at", "notes", "created_by", "created_at",
        ]
        read_only_fields = [
            "id", "years_of_service", "eosb_amount", "total_settlement",
            "created_by", "created_at",
        ]


# ─── Documents ────────────────────────────────────────────

class EmployeeDocumentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name_ar", read_only=True)

    class Meta:
        model = EmployeeDocument
        fields = [
            "id", "employee", "employee_name", "doc_type", "title",
            "file_name", "file_data", "issue_date", "expiry_date",
            "notes", "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_at"]


# ─── Saudization ──────────────────────────────────────────

class SaudizationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaudizationReport
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
