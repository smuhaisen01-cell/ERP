from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChartOfAccountViewSet,
    JournalEntryViewSet,
    VATReturnViewSet,
    ZakatReturnViewSet,
)

router = DefaultRouter()
router.register("chart-of-accounts", ChartOfAccountViewSet, basename="coa")
router.register("journal-entries", JournalEntryViewSet, basename="journal-entry")
router.register("vat-returns", VATReturnViewSet, basename="vat-return")
router.register("zakat-returns", ZakatReturnViewSet, basename="zakat-return")

urlpatterns = [
    path("", include(router.urls)),
]
