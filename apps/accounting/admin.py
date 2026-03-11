from django.contrib import admin
from .models import ChartOfAccount, JournalEntry, JournalEntryLine, VATReturn, ZakatReturn


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2


@admin.register(ChartOfAccount)
class ChartOfAccountAdmin(admin.ModelAdmin):
    list_display = ["code", "name_ar", "name_en", "account_type", "socpa_category", "is_active", "is_leaf"]
    list_filter = ["account_type", "socpa_category", "is_active"]
    search_fields = ["code", "name_ar", "name_en"]


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ["entry_number", "entry_date", "description_ar", "status", "created_by", "created_at"]
    list_filter = ["status", "entry_date"]
    search_fields = ["entry_number", "description_ar", "reference"]
    inlines = [JournalEntryLineInline]
    readonly_fields = ["created_at", "posted_at"]


@admin.register(VATReturn)
class VATReturnAdmin(admin.ModelAdmin):
    list_display = ["period_start", "period_end", "box_7_net_vat_due", "status"]
    list_filter = ["status"]


@admin.register(ZakatReturn)
class ZakatReturnAdmin(admin.ModelAdmin):
    list_display = ["fiscal_year", "zakat_due", "status"]
    list_filter = ["status"]
