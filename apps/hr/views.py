"""
HR API viewsets — Employee, Department, PayrollRun, Saudization.
"""
import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Department, Employee, PayrollRun, SaudizationReport
from .serializers import (
    DepartmentSerializer,
    EmployeeSerializer,
    EmployeeListSerializer,
    PayrollRunSerializer,
    SaudizationReportSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    search_fields = ["name_ar", "name_en", "cost_center"]


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("department").all()
    filterset_fields = ["nationality", "status", "department"]
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
        """Calculate GOSI contributions for this employee."""
        employee = self.get_object()
        return Response(employee.calculate_gosi())

    @action(detail=True, methods=["get"])
    def eosb(self, request, pk=None):
        """Calculate End of Service Benefit for this employee."""
        employee = self.get_object()
        return Response({
            "employee": employee.employee_number,
            "years_of_service": round((
                (employee.termination_date or timezone.now().date()) - employee.hire_date
            ).days / 365.25, 2),
            "eosb_amount_sar": str(employee.calculate_eosb()),
        })

    @action(detail=True, methods=["post"])
    def terminate(self, request, pk=None):
        """Terminate employee and calculate final EOSB."""
        employee = self.get_object()
        if employee.status == Employee.EmploymentStatus.TERMINATED:
            return Response({"error": "Employee is already terminated."}, status=status.HTTP_400_BAD_REQUEST)

        termination_date = request.data.get("termination_date", timezone.now().date().isoformat())
        employee.termination_date = termination_date
        employee.status = Employee.EmploymentStatus.TERMINATED
        employee.save()

        return Response({
            "employee": employee.employee_number,
            "status": "terminated",
            "termination_date": str(employee.termination_date),
            "final_eosb_sar": str(employee.calculate_eosb()),
        })


class PayrollRunViewSet(viewsets.ModelViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer
    filterset_fields = ["status", "period_year"]
    ordering = ["-period_year", "-period_month"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def calculate(self, request, pk=None):
        """
        Calculate payroll for all active employees.
        Computes gross, GOSI employer/employee, and net for the period.
        """
        payroll = self.get_object()
        if payroll.status != PayrollRun.Status.DRAFT:
            return Response({"error": "Only draft payrolls can be calculated."}, status=status.HTTP_400_BAD_REQUEST)

        employees = Employee.objects.filter(status=Employee.EmploymentStatus.ACTIVE)

        total_gross = Decimal("0")
        total_gosi_employer = Decimal("0")
        total_gosi_employee = Decimal("0")

        for emp in employees:
            total_gross += emp.gross_salary
            gosi = emp.calculate_gosi()
            total_gosi_employer += gosi["employer_contribution"]
            total_gosi_employee += gosi["employee_deduction"]

        payroll.total_gross = total_gross
        payroll.total_gosi_employer = total_gosi_employer
        payroll.total_gosi_employee = total_gosi_employee
        payroll.total_net = total_gross - total_gosi_employee
        payroll.save()

        return Response(PayrollRunSerializer(payroll).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve payroll run (draft → approved)."""
        payroll = self.get_object()
        if payroll.status != PayrollRun.Status.DRAFT:
            return Response({"error": "Only draft payrolls can be approved."}, status=status.HTTP_400_BAD_REQUEST)

        payroll.status = PayrollRun.Status.APPROVED
        payroll.approved_by = request.user
        payroll.save()
        return Response(PayrollRunSerializer(payroll).data)


class SaudizationReportViewSet(viewsets.ModelViewSet):
    queryset = SaudizationReport.objects.all()
    serializer_class = SaudizationReportSerializer
    ordering = ["-report_date"]

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate a Saudization report from current employee data."""
        employees = Employee.objects.filter(status=Employee.EmploymentStatus.ACTIVE)
        total = employees.count()
        saudi = employees.filter(nationality=Employee.Nationality.SAUDI).count()
        pct = Decimal(str(round(saudi / total * 100, 2))) if total > 0 else Decimal("0")

        # Determine Nitaqat band
        if pct >= 80:
            band = "platinum"
        elif pct >= 60:
            band = "high_green"
        elif pct >= 40:
            band = "medium_green"
        elif pct >= 25:
            band = "low_green"
        elif pct >= 10:
            band = "yellow"
        else:
            band = "red"

        report = SaudizationReport.objects.create(
            report_date=timezone.now().date(),
            total_employees=total,
            saudi_employees=saudi,
            saudization_percentage=pct,
            nitaqat_band=band,
        )
        return Response(SaudizationReportSerializer(report).data, status=status.HTTP_201_CREATED)
