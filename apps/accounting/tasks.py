"""
Accounting async tasks.
- daily_trial_balance_snapshot: Midnight snapshot for trend tracking
"""
import logging
from datetime import date
from celery import shared_task
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger("apps.accounting")


@shared_task(name="apps.accounting.tasks.daily_trial_balance_snapshot")
def daily_trial_balance_snapshot():
    """Midnight: Log trial balance for each tenant (for trend tracking)."""
    Tenant = get_tenant_model()
    tenants = Tenant.objects.filter(is_active=True).exclude(schema_name="public")
    for tenant in tenants:
        try:
            with tenant_context(tenant):
                from apps.accounting.models import JournalEntryLine
                from django.db.models import Sum

                agg = JournalEntryLine.objects.filter(
                    entry__status="posted"
                ).aggregate(
                    total_debit=Sum("debit_amount"),
                    total_credit=Sum("credit_amount"),
                )
                debit = agg["total_debit"] or 0
                credit = agg["total_credit"] or 0
                balanced = debit == credit

                logger.info(
                    f"[{tenant.schema_name}] TRIAL BALANCE: "
                    f"Debit={debit}, Credit={credit}, Balanced={balanced}"
                )
                # TODO: Store snapshot in a TrialBalanceSnapshot model for dashboards
        except Exception as e:
            logger.error(f"[{tenant.schema_name}] TB snapshot error: {e}")
    return "Trial balance snapshots logged"
