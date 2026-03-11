$content = @'
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import django.db
import pathlib


def health_check(request):
    try:
        django.db.connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    return JsonResponse({"status": "ok" if db_ok else "degraded"})


def debug_static(request):
    p = pathlib.Path('/app/staticfiles/spa/index.html')
    if p.exists():
        return HttpResponse('<pre>' + p.read_text()[:3000] + '</pre>')
    return HttpResponse('NOT FOUND')


urlpatterns = [
    path("debug/", debug_static),
    path("app/health/", health_check, name="health"),
    path("health/", health_check, name="health_root"),
    path("admin/", admin.site.urls),
]
