from django.urls import re_path
from .consumers.dashboard import AIDashboardConsumer

websocket_urlpatterns = [
    re_path(r"^ws/ai/dashboard/$", AIDashboardConsumer.as_asgi()),
]
