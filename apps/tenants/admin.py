"""Admin registrations for tenant models."""
from django.contrib import admin
from .models import Tenant, Domain


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name_ar", "name_en", "vat_number", "plan", "zatca_environment", "is_active", "created_at"]
    list_filter = ["plan", "zatca_environment", "is_active"]
    search_fields = ["name_ar", "name_en", "vat_number", "cr_number"]
    readonly_fields = ["schema_name", "created_at", "updated_at"]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "tenant", "is_primary"]
    list_filter = ["is_primary"]
