from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, POSTerminalViewSet, POSSessionViewSet, POSTransactionViewSet

router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branch")
router.register("terminals", POSTerminalViewSet, basename="terminal")
router.register("sessions", POSSessionViewSet, basename="session")
router.register("transactions", POSTransactionViewSet, basename="transaction")

urlpatterns = [
    path("", include(router.urls)),
]
