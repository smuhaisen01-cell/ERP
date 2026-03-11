from django.contrib import admin
from .models import Department, Employee, PayrollRun, SaudizationReport


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name_ar", "name_en", "cost_center"]
    search_fields = ["name_ar", "name_en"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["employee_number", "name_ar", "nationality", "department", "status", "basic_salary"]
    list_filter = ["nationality", "status", "department"]
    search_fields = ["employee_number", "name_ar", "name_en", "national_id"]
    readonly_fields = ["created_at"]


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ["period_year", "period_month", "status", "total_gross", "total_net"]
    list_filter = ["status", "period_year"]
    readonly_fields = ["created_at"]


@admin.register(SaudizationReport)
class SaudizationReportAdmin(admin.ModelAdmin):
    list_display = ["report_date", "total_employees", "saudi_employees", "saudization_percentage", "nitaqat_band"]
    list_filter = ["nitaqat_band"]
