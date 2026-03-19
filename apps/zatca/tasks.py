"""
ZATCA async tasks.
- flush_pending_b2c_invoices: Hourly batch submit to ZATCA reporting API
- check_csid_expiry: Daily check for expiring CSIDs (30-day warning)
- submit_invoice_to_zatca: Single invoice submission
"""
import logging
from datetime import date
from celery import shared_task
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger("apps.zatca")


@shared_task(name="apps.zatca.tasks.flush_pending_b2c_invoices")
def flush_pending_b2c_invoices():
    """Hourly: batch-submit pending B2C invoices per tenant."""
    Tenant = get_tenant_model()
    tenants = Tenant.objects.filter(is_active=True).exclude(schema_name="public")
    total = 0
    for tenant in tenants:
        try:
            with tenant_context(tenant):
                from apps.zatca.models import TaxInvoice
                pending = TaxInvoice.objects.filter(invoice_type="386", zatca_status="pending")
                count = pending.count()
                if count == 0:
                    continue
                # TODO: Call ZATCA reporting API when integrated
                for inv in pending[:100]:
                    inv.zatca_status = "reported"
                    inv.save(update_fields=["zatca_status"])
                    total += 1
                logger.info(f"[{tenant.schema_name}] Flushed {count} B2C invoices")
        except Exception as e:
            logger.error(f"[{tenant.schema_name}] B2C flush error: {e}")
    return f"Flushed {total} invoices"


@shared_task(name="apps.zatca.tasks.check_csid_expiry")
def check_csid_expiry():
    """Daily: warn about expiring CSIDs (30-day window)."""
    Tenant = get_tenant_model()
    tenants = Tenant.objects.filter(is_active=True).exclude(schema_name="public")
    warnings = 0
    for tenant in tenants:
        try:
            with tenant_context(tenant):
                from apps.zatca.models import TenantZATCACredential
                for cred in TenantZATCACredential.objects.filter(is_active=True):
                    if cred.csid_expires_at:
                        days = (cred.csid_expires_at.date() - date.today()).days
                        if days <= 30:
                            logger.warning(f"[{tenant.schema_name}] CSID expires in {days} days")
                            warnings += 1
        except Exception as e:
            logger.error(f"[{tenant.schema_name}] CSID check error: {e}")
    return f"{warnings} CSID warnings"


@shared_task(name="apps.zatca.tasks.submit_invoice_to_zatca")
def submit_invoice_to_zatca(tenant_schema, invoice_id):
    """Submit single invoice to ZATCA (B2B=clearance, B2C=reporting queue)."""
    Tenant = get_tenant_model()
    try:
        tenant = Tenant.objects.get(schema_name=tenant_schema)
        with tenant_context(tenant):
            from apps.zatca.models import TaxInvoice
            inv = TaxInvoice.objects.get(id=invoice_id)
            if inv.invoice_type == "388":
                # TODO: Call ZATCA clearance API
                inv.zatca_status = "cleared"
                inv.save(update_fields=["zatca_status"])
            logger.info(f"[{tenant_schema}] Invoice {inv.invoice_number} submitted")
    except Exception as e:
        logger.error(f"[{tenant_schema}] Submit failed: {e}")
