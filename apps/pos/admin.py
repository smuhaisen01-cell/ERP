from django.contrib import admin
from .models import Branch, POSTerminal, POSSession, POSTransaction, POSTransactionLine


class POSTransactionLineInline(admin.TabularInline):
    model = POSTransactionLine
    extra = 0


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["code", "name_ar", "city", "is_active"]
    search_fields = ["code", "name_ar"]


@admin.register(POSTerminal)
class POSTerminalAdmin(admin.ModelAdmin):
    list_display = ["terminal_id", "branch", "name", "is_active", "zatca_csid_registered"]
    list_filter = ["is_active", "zatca_csid_registered"]


@admin.register(POSSession)
class POSSessionAdmin(admin.ModelAdmin):
    list_display = ["terminal", "cashier", "opened_at", "status", "total_sales", "transaction_count"]
    list_filter = ["status"]


@admin.register(POSTransaction)
class POSTransactionAdmin(admin.ModelAdmin):
    list_display = ["transaction_number", "payment_method", "total_amount", "transacted_at"]
    list_filter = ["payment_method", "created_offline"]
    search_fields = ["transaction_number"]
    inlines = [POSTransactionLineInline]
