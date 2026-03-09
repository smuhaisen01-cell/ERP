from django.urls import path
from django.http import JsonResponse
from django.utils import timezone

def ai_health(request):
    return JsonResponse({"status": "ok", "service": "ai-platform", "timestamp": timezone.now().isoformat()})

urlpatterns = [
    path("health/", ai_health, name="ai_health"),
]
