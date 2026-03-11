"""
Tenant signals — triggered after a new tenant schema is created.
1. Grants ai_readonly SELECT on the new tenant schema.
2. Seeds SOCPA Chart of Accounts for the tenant.
"""
import logging
from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Tenant

logger = logging.getLogger("apps.tenants")


@receiver(post_save, sender=Tenant)
def on_tenant_created(sender, instance, created, **kwargs):
    """Post-save signal: runs after tenant schema is created by django-tenants."""
    if not created:
        return

    schema = instance.schema_name
    if schema == "public":
        return

    # 1. Grant ai_readonly SELECT on the new schema
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT grant_ai_readonly_on_tenant_schema(%s)", [schema])
        logger.info(f"Granted ai_readonly on schema: {schema}")
    except Exception as e:
        logger.warning(f"Could not grant ai_readonly on {schema}: {e}")

    # 2. Seed SOCPA Chart of Accounts
    try:
        from django.core.management import call_command
        from django_tenants.utils import schema_context
        with schema_context(schema):
            call_command("seed_socpa_coa", verbosity=0)
        logger.info(f"Seeded SOCPA CoA for tenant: {schema}")
    except Exception as e:
        logger.warning(f"Could not seed SOCPA CoA for {schema}: {e}")
