"""
Tenant async tasks.
- check_trial_expirations: Daily check for expiring trials
"""
import logging
from datetime import date, timedelta
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("apps.tenants")


@shared_task(name="apps.tenants.tasks.check_trial_expirations")
def check_trial_expirations():
    """Daily: Check for tenants whose trial is expiring or has expired."""
    from apps.tenants.models import Tenant

    now = timezone.now()
    warning_threshold = now + timedelta(days=7)

    # Expiring within 7 days
    expiring = Tenant.objects.filter(
        is_active=True,
        trial_ends_at__isnull=False,
        trial_ends_at__lte=warning_threshold,
        trial_ends_at__gt=now,
    )
    for t in expiring:
        days_left = (t.trial_ends_at - now).days
        logger.warning(f"TRIAL EXPIRING: {t.name_en} ({t.vat_number}) — {days_left} days left")
        # TODO: Send email notification

    # Already expired — deactivate
    expired = Tenant.objects.filter(
        is_active=True,
        trial_ends_at__isnull=False,
        trial_ends_at__lte=now,
    )
    expired_count = expired.count()
    if expired_count > 0:
        # Don't auto-deactivate yet — just log
        for t in expired:
            logger.warning(f"TRIAL EXPIRED: {t.name_en} ({t.vat_number}) — expired {t.trial_ends_at}")
        # TODO: Auto-deactivate after grace period

    return f"Expiring: {expiring.count()}, Expired: {expired_count}"
