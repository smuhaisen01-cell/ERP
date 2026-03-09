from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "timestamp": timezone.now().isoformat(),
        "service": "erp-core",
    })


urlpatterns = [
    # Health check — used by Docker, load balancers, ZATCA monitoring
    path("app/health/", health_check, name="health"),

    # Admin
    path("admin/", admin.site.urls),

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
