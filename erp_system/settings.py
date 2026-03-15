"""
Base settings for Saudi AI-ERP Platform.
All sensitive values loaded from environment via django-environ.
"""
import environ
from decimal import Decimal
from pathlib import Path

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    ENVIRONMENT=(str, "development"),
    AI_BACKEND=(str, "anthropic"),
    ZATCA_ENVIRONMENT=(str, "sandbox"),
    SUNAT_PRODUCTION=(bool, False),
)

BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / ".env")

# ─── Core ─────────────────────────────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
_allowed = env("ALLOWED_HOSTS")
# Railway health-check probes + common dev hosts
ALLOWED_HOSTS = _allowed + ["localhost", "127.0.0.1", ".railway.app", ".up.railway.app"]
ENVIRONMENT = env("ENVIRONMENT")

# ─── Saudi / ZATCA Constants ──────────────────────────────────────────────────
VAT_RATE = Decimal("0.15")           # Saudi VAT — 15%
ZAKAT_RATE = Decimal("0.025")        # Zakat on business assets — 2.5%
COMPANY_NAME = env("COMPANY_NAME", default="شركة تجريبية")
ZATCA_VAT_NUMBER = env("ZATCA_VAT_NUMBER", default="300000000000003")
ZATCA_ENVIRONMENT = env("ZATCA_ENVIRONMENT")  # sandbox | simulation | production
ZATCA_API_URL = env(
    "ZATCA_API_URL",
    default="https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal",
)
ZATCA_ENCRYPTION_KEY = env("ZATCA_ENCRYPTION_KEY", default="")

# ─── Multi-Tenancy (django-tenants) ───────────────────────────────────────────
SHARED_APPS = [
    "daphne",            # ASGI server — must be before django.contrib.staticfiles
    "django_tenants",
    "django.contrib.contenttypes",

    # Shared (public schema) apps
    "apps.tenants",      # Tenant + Domain models
    "apps.billing",      # Plans, subscriptions, Moyasar
    "apps.zatca",        # CSID credentials per tenant (public schema)

    # Django contrib (shared)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party (shared)
    "rest_framework",
    "corsheaders",
    "django_filters",
    "channels",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_celery_beat",
    "django_celery_results",
]

TENANT_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",

    # Core ERP apps (per-tenant schema)
    "apps.accounting",   # GL, CoA, SOCPA, AP/AR
    "apps.sales",        # Sales orders, CRM, invoicing
    "apps.inventory",    # Stock, warehouses, products
    "apps.hr",           # HR, Payroll, GOSI, Saudization
    "apps.pos",          # Point of Sale, offline-first
    "apps.zatca",        # TaxInvoice + lines (per-tenant)
    # AI Platform app (read-only — separate DB connection)
    "apps.ai",           # Copilot, forecasting, anomaly, alerts
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"
PUBLIC_SCHEMA_NAME = "public"

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# ─── Database ─────────────────────────────────────────────────────────────────
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://erp_readwrite:erp_primary_change_me@localhost:5432/erp_saas"),
}
DATABASES["default"]["ENGINE"] = "django_tenants.postgresql_backend"

# AI Platform uses a separate read-replica connection
AI_DATABASE_URL = env("AI_DATABASE_URL", default=env("DATABASE_URL", default=""))

# ─── Cache + Redis Streams ────────────────────────────────────────────────────
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "erp",
        "TIMEOUT": 300,
    }
}

# Redis Streams — event bus
REDIS_STREAM_PREFIX = "erp_events"       # Full key: erp_events:t_{vat_number}
REDIS_KPI_PREFIX = "kpi"                 # Full key: kpi:{tenant_id}
REDIS_ALERT_PREFIX = "alerts"            # Full key: alerts:{tenant_id}
REDIS_STREAM_MAXLEN = 10_000             # Max events per stream (trimmed)
REDIS_STREAM_RETENTION_DAYS = 7

# ─── Django Channels (WebSocket — Live Dashboard) ─────────────────────────────
ASGI_APPLICATION = "erp_system.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
            "capacity": 1500,
            "expiry": 10,
        },
    }
}

# ─── Celery ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Riyadh"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300          # 5 min hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 240

CELERY_TASK_ROUTES = {
    # ERP Core queues
    "apps.zatca.tasks.*":       {"queue": "zatca_clearance"},
    "apps.zatca.tasks.report*": {"queue": "zatca_reporting"},
    "apps.accounting.tasks.*":  {"queue": "default"},
    "apps.hr.tasks.*":          {"queue": "default"},

    # AI Platform queues (separate worker — read-only)
    "apps.ai.tasks.copilot*":   {"queue": "ai_inference"},
    "apps.ai.tasks.forecast*":  {"queue": "ai_batch"},
    "apps.ai.tasks.alert*":     {"queue": "ai_alerts"},
    "apps.ai.tasks.consume*":   {"queue": "event_consumer"},
}

# ─── Localization — Saudi Arabia ──────────────────────────────────────────────
LANGUAGE_CODE = "ar"
LANGUAGES = [
    ("ar", "العربية"),
    ("en", "English"),
]
TIME_ZONE = "Asia/Riyadh"
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

# ─── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "apps.tenants.middleware.ERPTenantMiddleware",  # MUST be first — resolves tenant from subdomain
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "erp_system.urls"
WSGI_APPLICATION = "erp_system.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.tenants.context_processors.tenant_context",
            ],
        },
    },
]

# ─── Static & Media ───────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
# Include React SPA build directory so collectstatic picks up assets
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─── REST Framework ───────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "300/minute",
        "anon": "30/minute",
    },
}

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
    "http://localhost:5173",    # Vite dev server
    "http://localhost:8000",
    "http://127.0.0.1:5173",
])
CORS_ALLOW_CREDENTIALS = True

# ─── Authentication ───────────────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
LOGIN_REDIRECT_URL = "/app/"
LOGOUT_REDIRECT_URL = "/"

# Google OAuth (optional)
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# ─── AI Platform Settings ─────────────────────────────────────────────────────
AI_BACKEND = env("AI_BACKEND")  # anthropic | ollama
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_MAX_TOKENS = 2048
OLLAMA_BASE_URL = env("OLLAMA_BASE_URL", default="http://ollama:11434")
OLLAMA_MODEL = env("OLLAMA_MODEL", default="command-r:35b")

AI_ANOMALY_THRESHOLD = 0.85       # Alert if anomaly score > this
AI_FORECAST_HORIZON_DAYS = 90     # Forecast 90 days ahead
AI_COPILOT_MAX_CONTEXT_ROWS = 100 # Max rows sent to LLM context

# ─── Cloudflare R2 (document storage) ────────────────────────────────────────
CLOUDFLARE_R2_BUCKET = env("CLOUDFLARE_R2_BUCKET", default="")
CLOUDFLARE_R2_ACCESS_KEY = env("CLOUDFLARE_R2_ACCESS_KEY", default="")
CLOUDFLARE_R2_SECRET_KEY = env("CLOUDFLARE_R2_SECRET_KEY", default="")
CLOUDFLARE_R2_ENDPOINT = env("CLOUDFLARE_R2_ENDPOINT", default="")
CLOUDFLARE_R2_PUBLIC_URL = env("CLOUDFLARE_R2_PUBLIC_URL", default="")

if CLOUDFLARE_R2_BUCKET:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_STORAGE_BUCKET_NAME = CLOUDFLARE_R2_BUCKET
    AWS_ACCESS_KEY_ID = CLOUDFLARE_R2_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY = CLOUDFLARE_R2_SECRET_KEY
    AWS_S3_ENDPOINT_URL = CLOUDFLARE_R2_ENDPOINT
    AWS_S3_CUSTOM_DOMAIN = CLOUDFLARE_R2_PUBLIC_URL
    AWS_DEFAULT_ACL = "private"

# ─── Moyasar Payment Gateway (Saudi — Mada, STC Pay) ─────────────────────────
MOYASAR_API_KEY = env("MOYASAR_API_KEY", default="")
MOYASAR_PUBLISHABLE_KEY = env("MOYASAR_PUBLISHABLE_KEY", default="")
MOYASAR_API_URL = "https://api.moyasar.com/v1"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
