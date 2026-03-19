"""
Celery configuration for Saudi AI-ERP.
Beat schedule runs periodic tasks: ZATCA B2C flush, CSID renewal, daily reports.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp_system.settings_production")

app = Celery("erp_system")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# ─── Beat Schedule ────────────────────────────────────────
app.conf.beat_schedule = {
    # ZATCA: Flush pending B2C invoices every hour
    "zatca-flush-b2c-hourly": {
        "task": "apps.zatca.tasks.flush_pending_b2c_invoices",
        "schedule": crontab(minute=0),  # Every hour at :00
    },

    # ZATCA: Check CSID expiry daily at 6 AM Riyadh
    "zatca-check-csid-expiry": {
        "task": "apps.zatca.tasks.check_csid_expiry",
        "schedule": crontab(hour=6, minute=0),
    },

    # HR: Send payroll reminder on 25th of each month at 9 AM
    "hr-payroll-reminder": {
        "task": "apps.hr.tasks.send_payroll_reminder",
        "schedule": crontab(day_of_month=25, hour=9, minute=0),
    },

    # HR: Check expiring documents daily at 8 AM
    "hr-check-expiring-docs": {
        "task": "apps.hr.tasks.check_expiring_documents",
        "schedule": crontab(hour=8, minute=0),
    },

    # HR: Auto attendance summary at end of day (6 PM Riyadh)
    "hr-daily-attendance-summary": {
        "task": "apps.hr.tasks.daily_attendance_summary",
        "schedule": crontab(hour=18, minute=0),
    },

    # Accounting: Daily trial balance snapshot at midnight
    "accounting-daily-snapshot": {
        "task": "apps.accounting.tasks.daily_trial_balance_snapshot",
        "schedule": crontab(hour=0, minute=0),
    },

    # Tenant: Check trial expirations daily at 7 AM
    "tenant-check-trials": {
        "task": "apps.tenants.tasks.check_trial_expirations",
        "schedule": crontab(hour=7, minute=0),
    },
}

app.conf.timezone = "Asia/Riyadh"


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
