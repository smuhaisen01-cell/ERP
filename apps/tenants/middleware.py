"""
Multi-tenant middleware — subdomain + custom domain routing.

Routing logic:
- Health/static/admin/signup → public schema (no DB query)
- /api/public/* → public schema (super-admin tenant management)
- Everything else → resolve tenant from Domain table via hostname
- Unknown domain → public schema (shows landing page)

Subdomain example: company1.erp.sa → Tenant with domain "company1.erp.sa"
Custom domain: erp.mycompany.com → Tenant with domain "erp.mycompany.com"
"""
from django.db import connection
from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import get_public_schema_name


# Paths that NEVER trigger tenant DB lookup
PUBLIC_PATHS = (
    "/health/",
    "/app/health/",
    "/static/",
    "/admin/",
    "/accounts/",
    "/favicon.ico",
    "/favicon.svg",
    "/assets/",
    "/api/public/",   # Super-admin APIs (public schema)
    "/signup/",
    "/landing/",
)


class ERPTenantMiddleware(TenantMainMiddleware):
    """
    Extends TenantMainMiddleware:
    1. Public paths → public schema without DB query
    2. Tenant paths → resolve from Domain table
    3. Unknown domains → public schema (landing page)
    """

    def process_request(self, request):
        path = request.path_info

        # ── Public paths: bypass tenant resolution ─────────────
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            connection.set_schema_to_public()
            request.tenant = _PublicTenantProxy()
            return None

        # ── Tenant resolution via domain lookup ────────────────
        try:
            return super().process_request(request)
        except self.TENANT_NOT_FOUND_EXCEPTION:
            # Unknown domain → public schema
            connection.set_schema_to_public()
            request.tenant = _PublicTenantProxy()
            return None


class _PublicTenantProxy:
    """Minimal stand-in when no tenant resolved."""
    schema_name = "public"
    name_ar = "Public"
    name_en = "Public"
    vat_number = ""
    plan = "starter"
    is_active = True

    def __str__(self):
        return "public"
