"""
Accounting serializers — ChartOfAccount, JournalEntry, VATReturn, ZakatReturn.
"""
from decimal import Decimal
from rest_framework import serializers
from .models import ChartOfAccount, JournalEntry, JournalEntryLine, VATReturn, ZakatReturn


class ChartOfAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartOfAccount
        fields = [
            "id", "code", "name_ar", "name_en", "account_type",
            "socpa_category", "parent", "is_active", "is_leaf",
            "normal_balance", "is_vat_account", "is_zakat_account",
        ]
        read_only_fields = ["id"]


class JournalEntryLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source="account.code", read_only=True)
    account_name = serializers.CharField(source="account.name_ar", read_only=True)

    class Meta:
        model = JournalEntryLine
        fields = [
            "id", "account", "account_code", "account_name",
            "description_ar", "debit_amount", "credit_amount", "cost_center",
        ]

    def validate(self, data):
        debit = data.get("debit_amount", Decimal("0"))
        credit = data.get("credit_amount", Decimal("0"))
        if debit > 0 and credit > 0:
            raise serializers.ValidationError(
                "A journal entry line cannot have both debit and credit amounts."
            )
        if debit == 0 and credit == 0:
            raise serializers.ValidationError(
                "A journal entry line must have either a debit or credit amount."
            )
        return data


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalEntryLineSerializer(many=True)
    is_balanced = serializers.BooleanField(read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id", "entry_number", "entry_date", "description_ar", "description_en",
            "reference", "status", "created_by", "posted_by", "posted_at",
            "created_at", "ai_anomaly_score", "ai_anomaly_flagged",
            "lines", "is_balanced",
        ]
        read_only_fields = [
            "id", "entry_number", "status", "created_by", "posted_by",
            "posted_at", "created_at", "ai_anomaly_score", "ai_anomaly_flagged",
        ]

    def validate_lines(self, lines_data):
        if len(lines_data) < 2:
            raise serializers.ValidationError("A journal entry must have at least 2 lines.")
        total_debit = sum(l.get("debit_amount", Decimal("0")) for l in lines_data)
        total_credit = sum(l.get("credit_amount", Decimal("0")) for l in lines_data)
        if total_debit != total_credit:
            raise serializers.ValidationError(
                f"Journal entry is not balanced: debits={total_debit}, credits={total_credit}"
            )
        return lines_data

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        entry = JournalEntry.objects.create(**validated_data)
        for line_data in lines_data:
            JournalEntryLine.objects.create(entry=entry, **line_data)
        return entry


class JournalEntryPostSerializer(serializers.Serializer):
    """Serializer for the POST action (status transition: draft → posted)."""
    pass


class VATReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = VATReturn
        fields = "__all__"
        read_only_fields = ["id", "created_at", "created_by"]


class ZakatReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZakatReturn
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
