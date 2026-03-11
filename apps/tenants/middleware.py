"""
Custom tenant middleware.

Key behaviour:
- Health check + admin + static paths → set schema to public WITHOUT any DB query.
  This is critical: Railway's health prober hits the container before any tenant
  exists in the DB, so any ORM query will fail on first deploy.
- All other paths → delegate to TenantMainMiddleware (subdomain resolution).
- Unknown domains → fall back to public schema instead of raising 404.
"""
from django.db import connection
from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import get_public_schema_name


# Paths that must NEVER trigger a DB query for tenant resolution.
# Health check must work even when the DB is empty (first deploy).
BYPASS_PATHS = (
    "/app/health/",
    "/health/",
    "/admin/",
    "/static/",
    "/accounts/",
    "/favicon.ico",
    "/app/", 
)


class ERPTenantMiddleware(TenantMainMiddleware):
    """
    Extends TenantMainMiddleware with two safety behaviours:
    1. Exempt paths get the public schema without ANY database query.
    2. Unknown tenant domains fall back to public schema (no 404 crash).
    """

    def process_request(self, request):
        path = request.path_info

        # ── Fast path: bypass tenant resolution entirely ──────────────────
        if any(path.startswith(p) for p in BYPASS_PATHS):
            # Set schema to public at the DB connection level — no ORM query.
            connection.set_schema_to_public()
            # Attach a minimal fake tenant object so downstream code doesn't crash
            # when it tries to read request.tenant.
            request.tenant = _PublicTenantProxy()
            return None  # Continue to next middleware

        # ── Normal path: let TenantMainMiddleware do subdomain lookup ─────
        try:
            return super().process_request(request)
        except self.TENANT_NOT_FOUND_EXCEPTION:
            # Unknown subdomain → serve public schema (API discovery, etc.)
            connection.set_schema_to_public()
            request.tenant = _PublicTenantProxy()
            return None


class _PublicTenantProxy:
    """
    Minimal stand-in for a Tenant object when no real tenant is resolved.
    Prevents AttributeError on request.tenant.schema_name etc.
    """
    schema_name = "public"
    name_ar = "Public"
    name_en = "Public"
    vat_number = ""
    plan = "starter"
    is_active = True

    def __str__(self):
        return "public"
