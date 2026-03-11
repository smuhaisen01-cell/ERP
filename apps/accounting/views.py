"""
Accounting API viewsets.
Follows SAP document-flow pattern: create (draft) → validate → post → reverse.
"""
import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import ChartOfAccount, JournalEntry, JournalEntryLine, VATReturn, ZakatReturn
from .serializers import (
    ChartOfAccountSerializer,
    JournalEntrySerializer,
    VATReturnSerializer,
    ZakatReturnSerializer,
)


class ChartOfAccountViewSet(viewsets.ModelViewSet):
    """
    SOCPA Chart of Accounts — per-tenant.
    Leaf accounts can receive journal entries; parent accounts are grouping only.
    """
    queryset = ChartOfAccount.objects.all()
    serializer_class = ChartOfAccountSerializer
    filterset_fields = ["account_type", "socpa_category", "is_active", "is_leaf"]
    search_fields = ["code", "name_ar", "name_en"]
    ordering_fields = ["code", "name_ar"]
    ordering = ["code"]


class JournalEntryViewSet(viewsets.ModelViewSet):
    """
    General Ledger Journal Entries.
    Status flow: draft → posted → reversed.
    AI has read-only access via ai_readonly PostgreSQL role.
    """
    queryset = JournalEntry.objects.prefetch_related("lines", "lines__account").all()
    serializer_class = JournalEntrySerializer
    filterset_fields = ["status", "entry_date"]
    search_fields = ["entry_number", "description_ar", "reference"]
    ordering_fields = ["entry_date", "created_at", "entry_number"]
    ordering = ["-entry_date"]

    def perform_create(self, serializer):
        # Auto-generate entry number
        entry_number = f"JE-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        serializer.save(created_by=self.request.user, entry_number=entry_number)

    @action(detail=True, methods=["post"])
    def post_entry(self, request, pk=None):
        """
        Transition: draft → posted.
        Validates balance, then marks as posted with audit trail.
        """
        entry = self.get_object()

        if entry.status != JournalEntry.Status.DRAFT:
            return Response(
                {"error": f"Cannot post entry with status '{entry.status}'. Must be 'draft'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not entry.is_balanced:
            return Response(
                {"error": "Journal entry is not balanced. Debits must equal credits."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            entry.status = JournalEntry.Status.POSTED
            entry.posted_by = request.user
            entry.posted_at = timezone.now()
            entry.save()

            # Publish event to Redis Stream for AI Platform
            self._publish_gl_event(entry)

        return Response(JournalEntrySerializer(entry).data)

    @action(detail=True, methods=["post"])
    def reverse_entry(self, request, pk=None):
        """
        Transition: posted → reversed.
        Creates a new reversing entry with swapped debits/credits.
        """
        entry = self.get_object()

        if entry.status != JournalEntry.Status.POSTED:
            return Response(
                {"error": "Only posted entries can be reversed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Mark original as reversed
            entry.status = JournalEntry.Status.REVERSED
            entry.save()

            # Create reversing entry
            rev_number = f"REV-{entry.entry_number}"
            reversing = JournalEntry.objects.create(
                entry_number=rev_number,
                entry_date=timezone.now().date(),
                description_ar=f"عكس قيد: {entry.entry_number}",
                description_en=f"Reversal of: {entry.entry_number}",
                reference=entry.entry_number,
                status=JournalEntry.Status.POSTED,
                created_by=request.user,
                posted_by=request.user,
                posted_at=timezone.now(),
            )
            # Swap debit/credit on each line
            for line in entry.lines.all():
                JournalEntryLine.objects.create(
                    entry=reversing,
                    account=line.account,
                    description_ar=f"عكس: {line.description_ar}",
                    debit_amount=line.credit_amount,
                    credit_amount=line.debit_amount,
                    cost_center=line.cost_center,
                )

        return Response(JournalEntrySerializer(reversing).data, status=status.HTTP_201_CREATED)

    def _publish_gl_event(self, entry):
        """Publish GL posting event to Redis Stream."""
        try:
            import redis
            import json
            from django.conf import settings
            from django_tenants.utils import get_tenant_model

            tenant = self.request.tenant
            if hasattr(tenant, "schema_name") and tenant.schema_name != "public":
                r = redis.from_url(settings.REDIS_URL)
                stream_key = f"{settings.REDIS_STREAM_PREFIX}:{tenant.schema_name}"
                r.xadd(stream_key, {
                    "event_type": "gl.entry_posted",
                    "payload": json.dumps({
                        "entry_number": entry.entry_number,
                        "entry_date": str(entry.entry_date),
                        "total_debit": str(sum(l.debit_amount for l in entry.lines.all())),
                    }),
                }, maxlen=settings.REDIS_STREAM_MAXLEN)
        except Exception:
            pass  # Non-critical — AI Platform will catch up


class VATReturnViewSet(viewsets.ModelViewSet):
    queryset = VATReturn.objects.all()
    serializer_class = VATReturnSerializer
    filterset_fields = ["status"]
    ordering = ["-period_start"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ZakatReturnViewSet(viewsets.ModelViewSet):
    queryset = ZakatReturn.objects.all()
    serializer_class = ZakatReturnSerializer
    ordering = ["-fiscal_year"]

    @action(detail=True, methods=["post"])
    def calculate(self, request, pk=None):
        """Recalculate zakat due based on current assets/liabilities."""
        zakat = self.get_object()
        zakat.calculate_zakat_due()
        zakat.save()
        return Response(ZakatReturnSerializer(zakat).data)
