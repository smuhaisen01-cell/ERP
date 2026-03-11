from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.utils import timezone
import django.db


def health_check(request):
    """
    Health endpoint for Railway / load balancers.
    Must respond 200 even when called with no subdomain (raw IP).
    Checks DB connectivity to give a real signal.
    """
    try:
        django.db.connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    status = "ok" if db_ok else "degraded"
    code = 200 if db_ok else 503
    return JsonResponse({
        "status": status,
        "timestamp": timezone.now().isoformat(),
        "service": "erp-core",
        "db": "ok" if db_ok else "error",
    }, status=code)


urlpatterns = [
    # Health check — Railway probes this; must be BEFORE any auth/tenant middleware
    path("app/health/", health_check, name="health"),
    path("health/", health_check, name="health_root"),  # fallback path

    # Admin
    path("admin/", admin.site.urls),
    path("debug/", debug_static),
    # Authentication (allauth)
    path("accounts/", include("allauth.urls")),

    # API v1
    path("api/v1/tenants/",    include("apps.tenants.urls")),
    path("api/v1/accounting/", include("apps.accounting.urls")),
    path("api/v1/zatca/",      include("apps.zatca.urls")),
    path("api/v1/sales/",      include("apps.sales.urls")),
    path("api/v1/inventory/",  include("apps.inventory.urls")),
    path("api/v1/hr/",         include("apps.hr.urls")),
    path("api/v1/pos/",        include("apps.pos.urls")),

    # AI Platform API
    path("ai/",                include("apps.ai.urls")),

    # Billing + Plans
    path("api/v1/billing/",    include("apps.billing.urls")),

    # Frontend SPA catch-all (React)
    path("app/", include("apps.tenants.spa_urls")),
]
from django.http import JsonResponse
import os

def debug_static(request):
    spa = '/app/static/spa/'
    staticfiles = '/app/staticfiles/spa/'
    return JsonResponse({
        'static_spa': os.listdir(spa) if os.path.exists(spa) else 'MISSING',
        'staticfiles_spa': os.listdir(staticfiles) if os.path.exists(staticfiles) else 'MISSING',
    })