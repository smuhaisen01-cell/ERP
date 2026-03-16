"""
ZATCA serializers — TaxInvoice, TaxInvoiceLine, ZATCAInvoiceLog.
"""
from rest_framework import serializers
from .models import TaxInvoice, TaxInvoiceLine, ZATCAInvoiceLog, TenantZATCACredential


class TaxInvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxInvoiceLine
        fields = [
            "id", "line_number", "description_ar", "description_en",
            "quantity", "unit", "unit_price", "discount_amount",
            "line_total", "vat_rate", "vat_amount", "vat_category_code",
        ]
        read_only_fields = ["id", "line_number"]


class TaxInvoiceSerializer(serializers.ModelSerializer):
    lines = TaxInvoiceLineSerializer(many=True)
    is_b2b = serializers.BooleanField(read_only=True)
    is_b2c = serializers.BooleanField(read_only=True)

    class Meta:
        model = TaxInvoice
        fields = [
            "id", "uuid", "invoice_number", "invoice_type", "invoice_type_code",
            "issue_date", "issue_time", "hijri_date",
            "buyer_name_ar", "buyer_vat_number", "buyer_cr_number", "buyer_address",
            "subtotal", "discount_total", "taxable_amount", "vat_amount", "total_amount",
            "invoice_hash", "previous_hash", "digital_signature", "qr_code_tlv",
            "zatca_status", "zatca_response_code", "zatca_response_message",
            "zatca_cleared_at", "zatca_submission_attempts",
            "created_by", "created_at", "is_cancelled",
            "lines", "is_b2b", "is_b2c",
        ]
        read_only_fields = [
            "id", "uuid", "invoice_number", "hijri_date",
            "invoice_hash", "previous_hash", "digital_signature", "qr_code_tlv",
            "zatca_status", "zatca_response_code", "zatca_response_message",
            "zatca_cleared_at", "zatca_submission_attempts",
            "created_by", "created_at",
        ]

    def validate_lines(self, lines_data):
        if not lines_data:
            raise serializers.ValidationError("An invoice must have at least 1 line item.")
        return lines_data

    def validate(self, data):
        # B2B invoices require buyer details
        if data.get("invoice_type") == TaxInvoice.InvoiceType.STANDARD:
            if not data.get("buyer_vat_number"):
                raise serializers.ValidationError(
                    {"buyer_vat_number": "VAT number is required for B2B (standard) invoices."}
                )
            if not data.get("buyer_name_ar"):
                raise serializers.ValidationError(
                    {"buyer_name_ar": "Buyer name is required for B2B invoices."}
                )
        return data

    def create(self, validated_data):
        import base64
        from datetime import datetime, timezone as tz

        lines_data = validated_data.pop("lines")

        # Generate QR (TLV tags 1-5) — no DB queries needed
        try:
            def tlv(tag, val):
                b = val.encode("utf-8")
                return bytes([tag, len(b)]) + b

            tlv_data = b""
            tlv_data += tlv(1, "Seller")
            tlv_data += tlv(2, "300000000000003")
            tlv_data += tlv(3, datetime.now(tz=tz.utc).isoformat())
            tlv_data += tlv(4, str(validated_data.get("total_amount", "0")))
            tlv_data += tlv(5, str(validated_data.get("vat_amount", "0")))
            validated_data["qr_code_tlv"] = base64.b64encode(tlv_data).decode()
        except Exception as e:
            print(f"QR ERROR: {e}")

        # Hijri date
        try:
            from hijri_converter import convert
            d = validated_data.get("issue_date")
            if d:
                h = convert.Gregorian(d.year, d.month, d.day).to_hijri()
                validated_data["hijri_date"] = f"{h.year:04d}-{h.month:02d}-{h.day:02d}"
        except Exception:
            pass

        invoice = TaxInvoice.objects.create(**validated_data)
        for idx, line_data in enumerate(lines_data, 1):
            TaxInvoiceLine.objects.create(invoice=invoice, line_number=idx, **line_data)
        return invoice

class TaxInvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views (no XML/signature fields)."""
    class Meta:
        model = TaxInvoice
        fields = [
            "id", "uuid", "invoice_number", "invoice_type",
            "issue_date", "buyer_name_ar", "total_amount", "vat_amount",
            "zatca_status", "created_at",
        ]


class ZATCAInvoiceLogSerializer(serializers.ModelSerializer):
    """Read-only audit log."""
    class Meta:
        model = ZATCAInvoiceLog
        fields = "__all__"


class TenantZATCACredentialSerializer(serializers.ModelSerializer):
    """Read-only — never expose private keys via API."""
    class Meta:
        model = TenantZATCACredential
        fields = [
            "id", "tenant_schema", "terminal_id", "credential_type",
            "environment", "issued_at", "expires_at", "is_active",
            "created_at", "renewed_at",
        ]
        # Explicitly exclude private_key_encrypted, binary_security_token, secret
