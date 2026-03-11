"""
HR serializers — Employee, Department, PayrollRun, SaudizationReport.
"""
from rest_framework import serializers
from .models import Department, Employee, PayrollRun, SaudizationReport


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
            "gross_salary", "is_saudi",
            "bank_name", "iban", "user",
            "gosi_breakdown", "eosb_amount",
            "created_at",
        ]
        read_only_fields = ["id", "employee_number", "created_at"]

    def get_gosi_breakdown(self, obj):
        return obj.calculate_gosi()

    def get_eosb_amount(self, obj):
        return str(obj.calculate_eosb())


class EmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight list view."""
    department_name = serializers.CharField(source="department.name_ar", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id", "employee_number", "name_ar", "nationality",
            "job_title_ar", "department_name", "status", "basic_salary",
        ]


class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = "__all__"
        read_only_fields = [
            "id", "total_gross", "total_gosi_employer", "total_gosi_employee",
            "total_net", "created_by", "created_at",
        ]


class SaudizationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaudizationReport
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
