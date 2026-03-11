# Commit-Ready Fixes — Saudi AI-ERP Platform

## Commit Message

```
fix: critical production blockers — 6 fixes across infrastructure, security, API, and ZATCA

BREAKING: Tenant middleware is now active. All requests are routed to tenant schemas.
Set up at least one Tenant + Domain in Django admin before accessing the app.

C6: Complete requirements.txt — added 15 missing dependencies
  - django-tenants, channels, channels-redis, daphne, django-redis
  - anthropic, hijri-converter, django-fsm, sentry-sdk
  - djangorestframework-simplejwt, django-celery-beat, django-celery-results

C1+C2: Enable tenant middleware + fix ALLOWED_HOSTS
  - Uncommented ERPTenantMiddleware (now position 1 in MIDDLEWARE)
  - Removed ALLOWED_HOSTS=['*'] from production settings
  - Added CORS_ALLOWED_ORIGINS configuration
  - Added daphne + channels to INSTALLED_APPS

H7: Fix railway.json deployment
  - Changed startCommand from gunicorn (WSGI) to daphne (ASGI)
  - WebSocket support now works on Railway

C5: Fix EOSB calculation bug
  - Decimal('1/3') → Decimal('1') / Decimal('3')
  - Was returning 0 for all employees with 2-5 years service

C3: Build complete DRF API layer
  - Accounting: ChartOfAccount, JournalEntry (with post/reverse actions), VATReturn, ZakatReturn
  - ZATCA: TaxInvoice (with process/submit/cancel actions), audit log (read-only), credentials
  - HR: Employee (with gosi/eosb/terminate actions), Department, PayrollRun, Saudization
  - POS: Branch, Terminal, Session (with close action), Transaction (auto-creates ZATCA invoice)
  - JWT authentication endpoints at /api/auth/token/
  - DRF throttling (300/min user, 30/min anon)

C4+H1: Fix ZATCA chain integrity + QR code
  - Added SELECT FOR UPDATE lock in invoice process to prevent chain hash forks
  - Removed TLV QR truncation on tags 7 (BST) and 8 (signature) — now sends full values
  - Fixed tag 2 to use actual VAT number instead of schema name
  - Added multi-byte TLV length encoding for values > 127 bytes

Bonus fixes:
  - Removed debug endpoint (path('debug/', debug_static))
  - Added admin registrations for ALL models across all 6 apps
  - Added tenant onboarding signal (ai_readonly grant + SOCPA CoA seed)
  - Added .dockerignore (prevents secret leakage and image bloat)
  - Removed stale root-level hr_models.py and settings.py duplicates
  - Added Sentry integration in production settings
```

## Files Changed (30 files)

### New Files (18)
- `.dockerignore`
- `apps/accounting/admin.py`
- `apps/accounting/serializers.py`
- `apps/accounting/views.py`
- `apps/hr/admin.py`
- `apps/hr/serializers.py`
- `apps/hr/views.py`
- `apps/pos/admin.py`
- `apps/pos/serializers.py`
- `apps/pos/views.py`
- `apps/tenants/admin.py`
- `apps/tenants/signals.py`
- `apps/zatca/admin.py`
- `apps/zatca/serializers.py`
- `apps/zatca/views.py`

### Modified Files (10)
- `requirements.txt` — 15 dependencies added
- `erp_system/settings.py` — middleware, CORS, INSTALLED_APPS, throttling
- `erp_system/settings_production.py` — ALLOWED_HOSTS, Sentry
- `erp_system/urls.py` — API routing, JWT, debug removal
- `railway.json` — gunicorn → daphne
- `apps/hr/models.py` — EOSB Decimal fix
- `apps/zatca/services.py` — QR fix, chain lock, process_invoice
- `apps/zatca/urls.py` — API routing
- `apps/hr/urls.py` — API routing
- `apps/accounting/urls.py` — API routing
- `apps/pos/urls.py` — API routing
- `apps/tenants/apps.py` — signals registration

### Deleted Files (2)
- `hr_models.py` (root-level duplicate)
- `settings.py` (root-level duplicate)
