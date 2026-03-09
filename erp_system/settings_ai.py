"""
AI Platform settings.
Identical to production EXCEPT:
  - DATABASE_URL points to the READ REPLICA
  - Only AI apps are active
  - No ERP write operations possible
"""
from .settings_production import *  # noqa
import environ

env = environ.Env()

# AI Platform connects to READ REPLICA only — compliance firewall
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://ai_readonly:ai_readonly_change_me@db-replica:5432/erp_saas",
    ),
}
# Keep django-tenants backend for schema routing
DATABASES["default"]["ENGINE"] = "django_tenants.postgresql_backend"

# AI Platform does not run ERP Celery tasks
CELERY_TASK_ROUTES = {
    "apps.ai.tasks.*":          {"queue": "ai_inference"},
    "apps.ai.tasks.forecast*":  {"queue": "ai_batch"},
    "apps.ai.tasks.alert*":     {"queue": "ai_alerts"},
    "apps.ai.tasks.consume*":   {"queue": "event_consumer"},
}

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["ai.yourdomain.sa", "localhost"])
