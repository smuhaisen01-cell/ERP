"""
POS API viewsets.
Key flow: open session → record sales → close session (Z-Report).
Each sale auto-creates a ZATCA simplified invoice (B2C).
"""
import uuid
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Branch, POSTerminal, POSSession, POSTransaction, POSTransactionLine
from .serializers import (
    BranchSerializer,
    POSTerminalSerializer,
    POSSessionSerializer,
    POSTransactionSerializer,
)
from apps.tenants.rbac import IsPOSCashierOrAdmin


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    permission_classes = [IsPOSCashierOrAdmin]
    serializer_class = BranchSerializer
    search_fields = ["code", "name_ar", "city"]


class POSTerminalViewSet(viewsets.ModelViewSet):
    queryset = POSTerminal.objects.select_related("branch").all()
    serializer_class = POSTerminalSerializer
    filterset_fields = ["branch", "is_active", "zatca_csid_registered"]
    permission_classes = [IsPOSCashierOrAdmin]

    @action(detail=False, methods=["post"])
    def setup_default(self, request):
        """Auto-create a default branch + terminal if none exist."""
        branch = Branch.objects.first()
        if not branch:
            branch = Branch.objects.create(
                code="MAIN",
                name_ar="الفرع الرئيسي",
                name_en="Main Branch",
                city="Riyadh",
                address_ar="الرياض",
            )
        terminal = POSTerminal.objects.first()
        if not terminal:
            terminal = POSTerminal.objects.create(
                terminal_id="MAIN-T01",
                branch=branch,
                name="Terminal 1",
            )
        return Response({
            "branch_id": branch.id,
            "terminal_id": terminal.id,
            "terminal_code": terminal.terminal_id,
        })


class POSSessionViewSet(viewsets.ModelViewSet):
    queryset = POSSession.objects.select_related("terminal", "cashier").all()
    serializer_class = POSSessionSerializer
    filterset_fields = ["terminal", "status"]
    ordering = ["-opened_at"]
    permission_classes = [IsPOSCashierOrAdmin]

    def perform_create(self, serializer):
        """Open a new POS session."""
        serializer.save(
            cashier=self.request.user,
            opened_at=timezone.now(),
        )

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """
        Close POS session — generates Z-Report totals.
        Aggregates all transactions in the session by payment method.
        """
        session = self.get_object()
        if session.status == POSSession.Status.CLOSED:
            return Response({"error": "Session is already closed."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            txns = session.transactions.all()
            agg = txns.aggregate(
                sales=Sum("total_amount"),
                vat=Sum("vat_amount"),
            )

            session.total_sales = agg["sales"] or Decimal("0")
            session.total_vat = agg["vat"] or Decimal("0")
            session.transaction_count = txns.count()

            # Aggregate by payment method
            for method, field in [
                ("cash", "total_cash"),
                ("mada", "total_mada"),
                ("stc_pay", "total_stc_pay"),
                ("credit_card", "total_credit_card"),
            ]:
                total = txns.filter(payment_method=method).aggregate(t=Sum("total_amount"))["t"]
                setattr(session, field, total or Decimal("0"))

            session.closing_cash = Decimal(request.data.get("closing_cash", "0"))
            session.status = POSSession.Status.CLOSED
            session.closed_at = timezone.now()
            session.save()

            # Publish event for AI Platform
            self._publish_session_closed(session)

        return Response(POSSessionSerializer(session).data)

    def _publish_session_closed(self, session):
        try:
            import redis as redis_lib
            import json
            from django.conf import settings

            tenant = self.request.tenant
            if hasattr(tenant, "schema_name") and tenant.schema_name != "public":
                r = redis_lib.from_url(settings.REDIS_URL)
                r.xadd(f"{settings.REDIS_STREAM_PREFIX}:{tenant.schema_name}", {
                    "event_type": "pos.session_closed",
                    "payload": json.dumps({
                        "session_total": str(session.total_sales),
                        "branch_code": session.terminal.branch.code,
                        "transaction_count": session.transaction_count,
                    }),
                }, maxlen=settings.REDIS_STREAM_MAXLEN)
        except Exception:
            pass


class POSTransactionViewSet(viewsets.ModelViewSet):
    """
    POS Transaction (sale). RBAC: POS Cashier + Admin.
    Creating a transaction auto-generates a ZATCA simplified invoice (B2C).
    """
    queryset = POSTransaction.objects.prefetch_related("lines").all()
    serializer_class = POSTransactionSerializer
    permission_classes = [IsPOSCashierOrAdmin]
    filterset_fields = ["session", "payment_method", "created_offline"]
    ordering = ["-transacted_at"]

    def perform_create(self, serializer):
        txn_number = f"POS-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        txn = serializer.save(
            transaction_number=txn_number,
            transacted_at=timezone.now(),
        )

        # Auto-create ZATCA simplified invoice (B2C) and queue for reporting
        self._create_zatca_invoice(txn)

        # Publish POS sale event for AI Platform
        self._publish_pos_sale(txn)

    def _create_zatca_invoice(self, txn):
        """Create a ZATCA simplified (B2C) invoice from this POS transaction."""
        try:
            from apps.zatca.models import TaxInvoice, TaxInvoiceLine

            invoice = TaxInvoice.objects.create(
                invoice_number=f"SINV-{txn.transaction_number}",
                invoice_type=TaxInvoice.InvoiceType.SIMPLIFIED,
                invoice_type_code="0200000",  # Simplified invoice
                issue_date=txn.transacted_at.date(),
                issue_time=txn.transacted_at.time(),
                hijri_date="",  # Will be set during process step
                subtotal=txn.subtotal,
                discount_total=txn.discount,
                taxable_amount=txn.subtotal - txn.discount,
                vat_amount=txn.vat_amount,
                total_amount=txn.total_amount,
                invoice_hash="",
                previous_hash="",
                digital_signature="",
                qr_code_tlv="",
                signed_xml="",
                created_by=txn.session.cashier,
            )

            for line in txn.lines.all():
                TaxInvoiceLine.objects.create(
                    invoice=invoice,
                    line_number=line.pk,
                    description_ar=line.product_name_ar,
                    description_en=line.product_name_en,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    discount_amount=line.discount_amount,
                    line_total=line.line_total,
                    vat_rate=line.vat_rate,
                    vat_amount=line.vat_amount,
                )

            # Link invoice to transaction
            txn.zatca_invoice = invoice
            txn.save(update_fields=["zatca_invoice"])

        except Exception:
            pass  # Log but don't fail the POS sale

    def _publish_pos_sale(self, txn):
        try:
            import redis as redis_lib
            import json
            from django.conf import settings

            tenant = self.request.tenant
            if hasattr(tenant, "schema_name") and tenant.schema_name != "public":
                r = redis_lib.from_url(settings.REDIS_URL)
                r.xadd(f"{settings.REDIS_STREAM_PREFIX}:{tenant.schema_name}", {
                    "event_type": "pos.sale",
                    "payload": json.dumps({
                        "transaction_number": txn.transaction_number,
                        "total_amount": str(txn.total_amount),
                        "vat_amount": str(txn.vat_amount),
                        "payment_method": txn.payment_method,
                    }),
                }, maxlen=settings.REDIS_STREAM_MAXLEN)
        except Exception:
            pass
