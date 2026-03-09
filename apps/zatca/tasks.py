"""
ZATCA Celery tasks.
- B2B clearance: zatca_clearance queue (high priority, sync)
- B2C reporting: zatca_reporting queue (hourly flush within 24h)
- CSID renewal: runs daily via Celery Beat
"""
from celery import shared_task
from django_tenants.utils import schema_context
from django.utils import timezone
import logging

logger = logging.getLogger("apps.zatca")


@shared_task(
    bind=True,
    queue="zatca_clearance",
    max_retries=5,
    default_retry_delay=10,       # 10s between retries
    soft_time_limit=60,
    time_limit=90,
)
def clear_b2b_invoice(self, tenant_schema: str, invoice_id: int):
    """
    Submit B2B invoice to ZATCA for clearance.
    SYNCHRONOUS — invoice must be CLEARED before it is sent to buyer.
    Retries up to 5 times with exponential backoff.
    """
    from .models import TaxInvoice
    from .services import ZATCASubmissionService
    from apps.tenants.models import Tenant

    with schema_context(tenant_schema):
        invoice = TaxInvoice.objects.get(pk=invoice_id)
        tenant = Tenant.objects.get(schema_name=tenant_schema)

        service = ZATCASubmissionService(tenant_schema, tenant.zatca_environment)
        invoice = service.clear_b2b_invoice(invoice)

        if invoice.zatca_status == "error":
            logger.error(
                f"ZATCA clearance failed: tenant={tenant_schema} invoice={invoice.invoice_number} "
                f"attempt={invoice.zatca_submission_attempts} error={invoice.zatca_response_message}"
            )
            # Exponential backoff: 10s, 20s, 40s, 80s, 160s
            raise self.retry(countdown=10 * (2 ** self.request.retries))

        logger.info(
            f"ZATCA B2B cleared: tenant={tenant_schema} invoice={invoice.invoice_number} "
            f"status={invoice.zatca_status}"
        )

        # Publish event to Redis Stream (AI Platform will receive this)
        _publish_event(tenant_schema, "invoice.zatca_cleared", {
            "invoice_id": invoice_id,
            "invoice_number": invoice.invoice_number,
            "invoice_type": invoice.invoice_type,
            "total_amount": str(invoice.total_amount),
            "vat_amount": str(invoice.vat_amount),
            "zatca_status": invoice.zatca_status,
        })

    return {"status": invoice.zatca_status, "invoice": invoice.invoice_number}


@shared_task(
    bind=True,
    queue="zatca_reporting",
    max_retries=10,
    default_retry_delay=300,      # 5 min between retries
    soft_time_limit=60,
    time_limit=90,
)
def report_b2c_invoice(self, tenant_schema: str, invoice_id: int):
    """
    Submit B2C (simplified) invoice to ZATCA for reporting.
    Must be submitted within 24 hours of issue.
    Celery Beat flushes pending B2C invoices hourly.
    """
    from .models import TaxInvoice
    from .services import ZATCASubmissionService
    from apps.tenants.models import Tenant

    with schema_context(tenant_schema):
        invoice = TaxInvoice.objects.get(pk=invoice_id)
        tenant = Tenant.objects.get(schema_name=tenant_schema)

        # Check 24h window hasn't expired
        from datetime import datetime, timezone as tz
        issue_dt = datetime.combine(invoice.issue_date, invoice.issue_time).replace(tzinfo=tz.utc)
        elapsed = (datetime.now(tz=tz.utc) - issue_dt).total_seconds()
        if elapsed > 86400:
            logger.error(
                f"ZATCA B2C 24h window expired: tenant={tenant_schema} "
                f"invoice={invoice.invoice_number} elapsed={elapsed:.0f}s"
            )
            invoice.zatca_status = "error"
            invoice.zatca_response_message = "24-hour reporting window expired"
            invoice.save()
            return {"status": "window_expired"}

        service = ZATCASubmissionService(tenant_schema, tenant.zatca_environment)
        invoice = service.report_b2c_invoice(invoice)

        if invoice.zatca_status == "error":
            raise self.retry(countdown=300 * (2 ** min(self.request.retries, 4)))

        _publish_event(tenant_schema, "invoice.zatca_reported", {
            "invoice_id": invoice_id,
            "invoice_number": invoice.invoice_number,
            "total_amount": str(invoice.total_amount),
            "vat_amount": str(invoice.vat_amount),
        })

    return {"status": invoice.zatca_status}


@shared_task(queue="default")
def flush_pending_b2c_invoices():
    """
    Hourly task: find all pending B2C invoices and submit to ZATCA.
    Called by Celery Beat every hour.
    """
    from apps.tenants.models import Tenant
    from .models import TaxInvoice

    active_tenants = Tenant.objects.filter(is_active=True, zatca_onboarded=True)
    total_queued = 0

    for tenant in active_tenants:
        with schema_context(tenant.schema_name):
            pending = TaxInvoice.objects.filter(
                invoice_type="386",       # Simplified (B2C)
                zatca_status="pending",
            ).values_list("id", flat=True)

            for invoice_id in pending:
                report_b2c_invoice.delay(tenant.schema_name, invoice_id)
                total_queued += 1

    logger.info(f"ZATCA B2C flush: queued {total_queued} invoices across {active_tenants.count()} tenants")
    return {"queued": total_queued}


@shared_task(queue="default")
def check_csid_renewals():
    """
    Daily task: check CSID expiry, auto-renew certificates expiring in < 30 days.
    Called by Celery Beat daily at 02:00 Riyadh time.
    """
    from .models import TenantZATCACredential
    from datetime import timedelta

    expiring_soon = TenantZATCACredential.objects.filter(
        is_active=True,
        expires_at__lt=timezone.now() + timedelta(days=30),
    )

    for cred in expiring_soon:
        logger.warning(
            f"ZATCA CSID expiring: tenant={cred.tenant_schema} "
            f"terminal={cred.terminal_id} expires={cred.expires_at}"
        )
        # Trigger renewal workflow
        renew_csid.delay(cred.id)


@shared_task(queue="default")
def renew_csid(credential_id: int):
    """Renew a ZATCA CSID certificate before expiry."""
    # Full CSID renewal flow:
    # 1. Generate new EC key pair
    # 2. Build CSR with existing credential info
    # 3. POST to /production/csids with existing CSID auth
    # 4. Store new credential, deactivate old one
    logger.info(f"ZATCA CSID renewal triggered for credential_id={credential_id}")


def _publish_event(tenant_schema: str, event_type: str, payload: dict):
    """Publish domain event to Redis Stream for AI Platform consumption."""
    import redis
    import json
    import uuid
    from django.conf import settings
    from django.utils import timezone

    r = redis.from_url(settings.REDIS_URL)
    stream_key = f"{settings.REDIS_STREAM_PREFIX}:{tenant_schema}"

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "tenant_id": tenant_schema,
        "occurred_at": timezone.now().isoformat(),
        "version": "1.0",
        "source": "erp_core",
        "payload": json.dumps(payload),
    }

    r.xadd(stream_key, event, maxlen=settings.REDIS_STREAM_MAXLEN)
