from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaxInvoiceViewSet, ZATCAInvoiceLogViewSet, TenantZATCACredentialViewSet

router = DefaultRouter()
router.register("invoices", TaxInvoiceViewSet, basename="tax-invoice")
router.register("audit-log", ZATCAInvoiceLogViewSet, basename="zatca-log")
router.register("credentials", TenantZATCACredentialViewSet, basename="zatca-credential")

urlpatterns = [
    path("", include(router.urls)),
]
