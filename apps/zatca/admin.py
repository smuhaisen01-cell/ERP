from django.contrib import admin
from .models import TenantZATCACredential, TaxInvoice, TaxInvoiceLine, ZATCAInvoiceLog


class TaxInvoiceLineInline(admin.TabularInline):
    model = TaxInvoiceLine
    extra = 0
    readonly_fields = ["line_number"]


@admin.register(TenantZATCACredential)
class TenantZATCACredentialAdmin(admin.ModelAdmin):
    list_display = ["tenant_schema", "terminal_id", "credential_type", "environment", "is_active", "expires_at"]
    list_filter = ["environment", "is_active", "credential_type"]
    search_fields = ["tenant_schema", "terminal_id"]
    # Never display private_key_encrypted in admin
    exclude = ["private_key_encrypted"]


@admin.register(TaxInvoice)
class TaxInvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "invoice_type", "issue_date", "total_amount", "zatca_status", "created_at"]
    list_filter = ["invoice_type", "zatca_status", "is_cancelled"]
    search_fields = ["invoice_number", "buyer_name_ar", "buyer_vat_number"]
    readonly_fields = ["uuid", "invoice_hash", "previous_hash", "digital_signature", "qr_code_tlv", "created_at"]
    inlines = [TaxInvoiceLineInline]


@admin.register(ZATCAInvoiceLog)
class ZATCAInvoiceLogAdmin(admin.ModelAdmin):
    """Read-only admin for immutable audit log."""
    list_display = ["invoice_number", "invoice_type", "tenant_schema", "zatca_status", "total_amount", "logged_at"]
    list_filter = ["zatca_status", "environment"]
    search_fields = ["invoice_number", "tenant_schema"]
    readonly_fields = [f.name for f in ZATCAInvoiceLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
