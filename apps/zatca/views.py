"""
ZATCA API viewsets.
Invoice flow: create → process (sign/hash/QR) → submit to ZATCA.
B2B: synchronous clearance via Celery task.
B2C: async reporting queued for hourly flush.
"""
import uuid as uuid_lib
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import TaxInvoice, TaxInvoiceLine, ZATCAInvoiceLog, TenantZATCACredential
from .serializers import (
    TaxInvoiceSerializer,
    TaxInvoiceListSerializer,
    ZATCAInvoiceLogSerializer,
    TenantZATCACredentialSerializer,
)
from apps.tenants.rbac import IsAccountantOrAdmin


class TaxInvoiceViewSet(viewsets.ModelViewSet):
    """
    Tax Invoice management. RBAC: Accountant + Admin only.
    """
    queryset = TaxInvoice.objects.prefetch_related("lines").all()
    permission_classes = [IsAccountantOrAdmin]
    filterset_fields = ["invoice_type", "zatca_status", "issue_date", "is_cancelled"]
    search_fields = ["invoice_number", "buyer_name_ar", "buyer_vat_number"]
    ordering_fields = ["issue_date", "created_at", "total_amount"]
    ordering = ["-issue_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return TaxInvoiceListSerializer
        return TaxInvoiceSerializer

    def perform_create(self, serializer):
        invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{uuid_lib.uuid4().hex[:6].upper()}"
        invoice = serializer.save(
            created_by=self.request.user,
            invoice_number=invoice_number,
        )
        # Auto-generate basic QR code (ZATCA Phase 1 TLV format)
        self._generate_basic_qr(invoice)

    def _generate_basic_qr(self, invoice):
        """Generate basic TLV QR code without ZATCA credentials (Phase 1 compatible)."""
        try:
            import base64
            from datetime import datetime, timezone as tz

            tenant = self.request.tenant
            seller_name = getattr(tenant, 'name_ar', 'Seller')
            vat_number = getattr(tenant, 'vat_number', '300000000000003')

            def tlv_tag(tag, value_bytes):
                length = len(value_bytes)
                if length <= 127:
                    return bytes([tag, length]) + value_bytes
                len_bytes = length.to_bytes((length.bit_length() + 7) // 8, "big")
                return bytes([tag, 0x80 | len(len_bytes)]) + len_bytes + value_bytes

            tlv = b""
            tlv += tlv_tag(1, seller_name.encode("utf-8"))
            tlv += tlv_tag(2, vat_number.encode("utf-8"))
            tlv += tlv_tag(3, datetime.now(tz=tz.utc).isoformat().encode("utf-8"))
            tlv += tlv_tag(4, str(invoice.total_amount).encode("utf-8"))
            tlv += tlv_tag(5, str(invoice.vat_amount).encode("utf-8"))

            invoice.qr_code_tlv = base64.b64encode(tlv).decode()

            # Set hijri date
            try:
                from hijri_converter import convert
                hijri = convert.Gregorian(
                    invoice.issue_date.year,
                    invoice.issue_date.month,
                    invoice.issue_date.day,
                ).to_hijri()
                invoice.hijri_date = f"{hijri.year:04d}-{hijri.month:02d}-{hijri.day:02d}"
            except Exception:
                invoice.hijri_date = ""

            invoice.save(update_fields=["qr_code_tlv", "hijri_date"])

            # Auto-create GL journal entry for this invoice
            self._create_gl_entry(invoice)
        except Exception as e:
            import logging
            logging.getLogger("apps.zatca").warning(f"QR generation failed: {e}")

    def _create_gl_entry(self, invoice):
        """Auto-create a journal entry for the invoice (Revenue + VAT + AR)."""
        try:
            from apps.accounting.models import ChartOfAccount, JournalEntry, JournalEntryLine
            import uuid as uuid_mod

            # Find accounts by code (seeded by SOCPA)
            ar_account = ChartOfAccount.objects.filter(code='1121').first()  # Trade Receivables
            revenue_account = ChartOfAccount.objects.filter(code='4100').first()  # Sales Revenue
            vat_account = ChartOfAccount.objects.filter(code='2120').first()  # VAT Output

            if not (ar_account and revenue_account and vat_account):
                return  # Accounts not seeded yet

            entry = JournalEntry.objects.create(
                entry_number=f"JE-{invoice.invoice_number}",
                entry_date=invoice.issue_date,
                description_ar=f"فاتورة {invoice.invoice_number}",
                description_en=f"Invoice {invoice.invoice_number}",
                reference=invoice.invoice_number,
                status='posted',
                created_by=invoice.created_by,
                posted_by=invoice.created_by,
                posted_at=timezone.now(),
            )

            # Debit: Accounts Receivable (total)
            JournalEntryLine.objects.create(
                entry=entry,
                account=ar_account,
                description_ar=f"ذمم مدينة — {invoice.invoice_number}",
                debit_amount=invoice.total_amount,
                credit_amount=0,
            )
            # Credit: Revenue (subtotal)
            JournalEntryLine.objects.create(
                entry=entry,
                account=revenue_account,
                description_ar=f"إيرادات — {invoice.invoice_number}",
                debit_amount=0,
                credit_amount=invoice.taxable_amount,
            )
            # Credit: VAT Output (vat)
            JournalEntryLine.objects.create(
                entry=entry,
                account=vat_account,
                description_ar=f"ضريبة مخرجات — {invoice.invoice_number}",
                debit_amount=0,
                credit_amount=invoice.vat_amount,
            )
        except Exception as e:
            import logging
            logging.getLogger("apps.zatca").warning(f"Auto GL entry failed: {e}")

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """
        Process invoice: build UBL XML → compute hash → sign → generate QR.
        Must be called before submit. Uses a per-tenant lock to prevent chain forks.
        """
        invoice = self.get_object()

        if invoice.zatca_status != TaxInvoice.ZATCAStatus.PENDING:
            return Response(
                {"error": f"Invoice already processed (status: {invoice.zatca_status})."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tenant = request.tenant
        if not hasattr(tenant, "schema_name") or tenant.schema_name == "public":
            return Response(
                {"error": "Invoice processing requires a valid tenant context."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from .services import FatooraService
            # Atomic lock: prevent concurrent invoice processing for the same tenant
            # to protect chain hash integrity (Fix C4)
            with transaction.atomic():
                # Lock the last audit log row to serialize chain access
                last_log = (
                    ZATCAInvoiceLog.objects
                    .filter(tenant_schema=tenant.schema_name)
                    .select_for_update()
                    .order_by("-logged_at")
                    .first()
                )

                terminal_id = request.data.get("terminal_id", "")
                service = FatooraService(tenant.schema_name, terminal_id)
                invoice = service.process_invoice(invoice)

        except TenantZATCACredential.DoesNotExist:
            return Response(
                {"error": "No active ZATCA credential found for this tenant/terminal."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Invoice processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(TaxInvoiceSerializer(invoice).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """
        Submit processed invoice to ZATCA.
        B2B → clear_b2b_invoice Celery task (synchronous clearance).
        B2C → report_b2c_invoice Celery task (async, 24h window).
        """
        invoice = self.get_object()

        if not invoice.invoice_hash:
            return Response(
                {"error": "Invoice must be processed before submission. Call /process/ first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invoice.zatca_status not in (
            TaxInvoice.ZATCAStatus.PENDING,
            TaxInvoice.ZATCAStatus.ERROR,
        ):
            return Response(
                {"error": f"Invoice cannot be resubmitted (status: {invoice.zatca_status})."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tenant = request.tenant
        from .tasks import clear_b2b_invoice, report_b2c_invoice

        if invoice.is_b2b:
            clear_b2b_invoice.delay(tenant.schema_name, invoice.id)
            return Response({"message": "B2B clearance task queued.", "invoice": invoice.invoice_number})
        else:
            report_b2c_invoice.delay(tenant.schema_name, invoice.id)
            return Response({"message": "B2C reporting task queued.", "invoice": invoice.invoice_number})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Mark invoice as cancelled. Requires a credit note for ZATCA."""
        invoice = self.get_object()
        if invoice.is_cancelled:
            return Response({"error": "Invoice is already cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        invoice.is_cancelled = True
        invoice.save()
        return Response(TaxInvoiceSerializer(invoice).data)


class ZATCAInvoiceLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    IMMUTABLE audit log — read-only API.
    5-year retention required by Saudi law.
    """
    queryset = ZATCAInvoiceLog.objects.all()
    serializer_class = ZATCAInvoiceLogSerializer
    filterset_fields = ["tenant_schema", "invoice_type", "zatca_status", "environment"]
    search_fields = ["invoice_number"]
    ordering = ["-logged_at"]


class TenantZATCACredentialViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    ZATCA credentials — read-only (no private keys exposed).
    Used to check credential status and expiry dates.
    """
    queryset = TenantZATCACredential.objects.all()
    serializer_class = TenantZATCACredentialSerializer
    filterset_fields = ["environment", "is_active", "credential_type"]
