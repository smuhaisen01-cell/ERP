from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, EmployeeViewSet,
    LeaveTypeViewSet, LeaveRequestViewSet,
    AttendanceViewSet,
    PayrollRunViewSet,
    TerminationSettlementViewSet,
    EmployeeDocumentViewSet,
    SaudizationReportViewSet,
)

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="department")
router.register("employees", EmployeeViewSet, basename="employee")
router.register("leave-types", LeaveTypeViewSet, basename="leave-type")
router.register("leave-requests", LeaveRequestViewSet, basename="leave-request")
router.register("attendance", AttendanceViewSet, basename="attendance")
router.register("payroll-runs", PayrollRunViewSet, basename="payroll-run")
router.register("terminations", TerminationSettlementViewSet, basename="termination")
router.register("documents", EmployeeDocumentViewSet, basename="employee-document")
router.register("saudization", SaudizationReportViewSet, basename="saudization")

urlpatterns = [
    path("", include(router.urls)),
]
