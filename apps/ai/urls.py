from django.urls import path
from .views import (
    CopilotChatView, DashboardQAView, SmartAlertsView,
    ForecastView, AutoCategorizeView, AIStatusView,
)

urlpatterns = [
    path("chat/", CopilotChatView.as_view(), name="ai-chat"),
    path("dashboard-qa/", DashboardQAView.as_view(), name="ai-dashboard-qa"),
    path("alerts/", SmartAlertsView.as_view(), name="ai-alerts"),
    path("forecast/", ForecastView.as_view(), name="ai-forecast"),
    path("categorize/", AutoCategorizeView.as_view(), name="ai-categorize"),
    path("status/", AIStatusView.as_view(), name="ai-status"),
]
