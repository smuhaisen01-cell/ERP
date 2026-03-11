from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, EmployeeViewSet, PayrollRunViewSet, SaudizationReportViewSet

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="department")
router.register("employees", EmployeeViewSet, basename="employee")
router.register("payroll-runs", PayrollRunViewSet, basename="payroll-run")
router.register("saudization", SaudizationReportViewSet, basename="saudization")

urlpatterns = [
    path("", include(router.urls)),
]
