"""
Public-schema API URLs — tenant provisioning + super-admin management.
Mounted at /api/public/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .provisioning import signup, TenantViewSet

router = DefaultRouter()
router.register("tenants", TenantViewSet, basename="tenant")

urlpatterns = [
    path("signup/", signup, name="tenant-signup"),
    path("", include(router.urls)),
]
