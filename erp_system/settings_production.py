"""Production settings — inherits base, adds security hardening."""
from .settings import *  # noqa
import os

DEBUG = False

# Railway's internal health prober hits containers directly via internal IP over plain HTTP.
# We rely on Cloudflare + Railway's edge for host validation — safe to wildcard here.
ALLOWED_HOSTS = ["*"]

# ─── Security ─────────────────────────────────────────────────────────────────
# Railway terminates TLS at the edge. Internal container traffic is plain HTTP.
# SECURE_SSL_REDIRECT=True causes 301 redirect loops on the health prober.
# Real HTTPS enforcement is handled by Railway's edge + Cloudflare.
SECURE_SSL_REDIRECT = False

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps.zatca": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps.ai": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
