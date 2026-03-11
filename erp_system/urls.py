from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.utils import timezone
import django.db
import os


def health_check(request):
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


def debug_static(request):
    spa = '/app/static/spa/'
    staticfiles = '/app/staticfiles/spa/'
    return JsonResponse({
        'static_spa': os.listdir(spa) if os.path.exists(spa) else 'MISSING',
        'staticfiles_spa': os.listdir(staticfiles) if os.path.exists(staticfiles) else 'MISSING',
    })


urlpatterns = [
    path("debug/", debug_static),
    path("app/health/", health_check, name="health"),
    path("health/", health_check, name="health_root"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("api/v1/tenants/",    include("apps.tenants.urls")),
    path("api/v1/accounting/", include("apps.accounting.urls")),
    path("api/v1/zatca/",      include("apps.zatca.urls")),
    path("api/v1/sales/",      include("apps.sales.urls")),
    path("api/v1/inventory/",  include("apps.inventory.urls")),
    path("api/v1/hr/",         include("apps.hr.urls")),
    path("api/v1/pos/",        include("apps.pos.urls")),
    path("ai/",                include("apps.ai.urls")),
    path("api/v1/billing/",    include("apps.billing.urls")),
    path("app/", include("apps.tenants.spa_urls")),
]