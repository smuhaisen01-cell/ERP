import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Tenant

logger = logging.getLogger("apps.tenants")


@receiver(post_save, sender=Tenant)
def on_tenant_created(sender, instance, created, **kwargs):
    if created and instance.schema_name != "public":
        logger.info(f"New tenant created: {instance.schema_name}")