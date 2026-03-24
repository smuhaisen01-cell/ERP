"""
Saudi AI-ERP — Root URL configuration.
API is mounted at /api/{module}/ — all endpoints require JWT authentication.
SPA is served at /app/ via a catch-all that serves index.html.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.utils import timezone
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
import django.db


def health_check(request):
    """Health check — used by Railway, Docker, and load balancers."""
    try:
        django.db.connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    return JsonResponse({
        "status": "ok" if db_ok else "degraded",
        "timestamp": timezone.now().isoformat(),
    })


def api_root(request):
    """API discovery endpoint."""
    return JsonResponse({
        "service": "Saudi AI-ERP Platform",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth/token/",
            "accounting": "/api/accounting/",
            "zatca": "/api/zatca/",
            "hr": "/api/hr/",
            "pos": "/api/pos/",
            "ai": "/api/ai/",
        },
    })


urlpatterns = [
    # ─── Health ───────────────────────────────────────────────
    path("health/", health_check, name="health_root"),
    path("app/health/", health_check, name="health"),

    # ─── Public API (no tenant resolution) ──────────────────
    path("api/public/", include("apps.tenants.public_urls")),

    # ─── Authentication (JWT) ─────────────────────────────────
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # ─── API Modules ──────────────────────────────────────────
    path("api/", api_root, name="api_root"),
    path("api/accounting/", include("apps.accounting.urls")),
    path("api/reports/", include("apps.accounting.report_urls")),
    path("api/zatca/", include("apps.zatca.urls")),
    path("api/hr/", include("apps.hr.urls")),
    path("api/pos/", include("apps.pos.urls")),
    path("api/inventory/", include("apps.inventory.urls")),
    path("api/users/", include("apps.tenants.user_urls")),
    path("api/ai/", include("apps.ai.urls")),

    # ─── Django Admin ─────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ─── React SPA (catch-all — must be last) ─────────────────
    path("app/", include("apps.tenants.spa_urls")),
]
