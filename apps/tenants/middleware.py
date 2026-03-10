"""
Custom tenant middleware.
Falls back to the 'public' schema for:
  - Health check endpoints
  - Admin
  - Static files
  - Any request that can't be matched to a tenant domain

This prevents 404/500 errors on Railway health checks and direct IP access.
"""
from django.db import connection
from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import get_public_schema_name


EXEMPT_PATHS = (
    "/app/health/",
    "/health/",
    "/admin/",
    "/static/",
    "/accounts/",
    "/favicon.ico",
)


class ERPTenantMiddleware(TenantMainMiddleware):
    """
    Extends TenantMainMiddleware to handle:
    1. Health-check / admin paths → always use public schema
    2. Unknown domains → fall back to public schema instead of raising 404
    """

    def process_request(self, request):
        # Fast-path: exempt paths always get public schema
        path = request.path_info
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            connection.set_schema_to_public()
            from django_tenants.utils import get_tenant_model
            TenantModel = get_tenant_model()
            try:
                tenant = TenantModel.objects.get(
                    schema_name=get_public_schema_name()
                )
                request.tenant = tenant
            except TenantModel.DoesNotExist:
                # Public tenant not created yet — still serve health check
                connection.set_schema_to_public()
                return None
            return None

        try:
            return super().process_request(request)
        except self.TENANT_NOT_FOUND_EXCEPTION:
            # Unknown subdomain → fall back to public schema
            connection.set_schema_to_public()
            return None
