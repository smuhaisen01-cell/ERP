from django.contrib import admin
from .models import (
    Department, Employee, LeaveType, LeaveRequest, Attendance,
    PayrollRun, PayrollLine, TerminationSettlement, EmployeeDocument,
    SaudizationReport,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name_ar", "name_en", "cost_center"]


class PayrollLineInline(admin.TabularInline):
    model = PayrollLine
    extra = 0
    readonly_fields = ["employee", "gross_salary", "net_salary"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["employee_number", "name_ar", "nationality", "department", "status", "basic_salary"]
    list_filter = ["nationality", "status", "department", "contract_type"]
    search_fields = ["employee_number", "name_ar", "name_en", "national_id"]


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ["name_ar", "name_en", "code", "default_days", "is_paid"]


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "start_date", "end_date", "days", "status"]
    list_filter = ["status", "leave_type"]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["employee", "date", "check_in", "check_out", "status", "hours_worked"]
    list_filter = ["status", "date"]


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ["period_year", "period_month", "status", "employee_count", "total_gross", "total_net"]
    list_filter = ["status", "period_year"]
    inlines = [PayrollLineInline]


@admin.register(TerminationSettlement)
class TerminationSettlementAdmin(admin.ModelAdmin):
    list_display = ["employee", "termination_date", "reason", "eosb_amount", "total_settlement", "is_paid"]
    list_filter = ["reason", "is_paid"]


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ["employee", "doc_type", "title", "expiry_date"]
    list_filter = ["doc_type"]


@admin.register(SaudizationReport)
class SaudizationReportAdmin(admin.ModelAdmin):
    list_display = ["report_date", "total_employees", "saudi_employees", "saudization_percentage", "nitaqat_band"]
