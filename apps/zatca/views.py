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


class TaxInvoiceViewSet(viewsets.ModelViewSet):
    """
    Tax Invoice management.
    POST /api/zatca/invoices/ — create invoice
    POST /api/zatca/invoices/{id}/process/ — sign, hash, QR
    POST /api/zatca/invoices/{id}/submit/ — submit to ZATCA
    """
    queryset = TaxInvoice.objects.prefetch_related("lines").all()
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
        serializer.save(
            created_by=self.request.user,
            invoice_number=invoice_number,
        )

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
