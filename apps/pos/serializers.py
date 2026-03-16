"""
POS serializers — Branch, Terminal, Session, Transaction.
"""
from rest_framework import serializers
from .models import Branch, POSTerminal, POSSession, POSTransaction, POSTransactionLine


class BranchSerializer(serializers.ModelSerializer):
    terminal_count = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = ["id", "code", "name_ar", "name_en", "city", "address_ar", "is_active", "terminal_count"]

    def get_terminal_count(self, obj):
        return obj.terminals.filter(is_active=True).count()


class POSTerminalSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name_ar", read_only=True)

    class Meta:
        model = POSTerminal
        fields = [
            "id", "terminal_id", "branch", "branch_name", "name",
            "is_active", "zatca_csid_registered", "zatca_registered_at",
        ]
        read_only_fields = ["id", "zatca_csid_registered", "zatca_registered_at"]


class POSTransactionLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSTransactionLine
        fields = [
            "id", "product_code", "product_name_ar", "product_name_en",
            "quantity", "unit_price", "discount_amount",
            "vat_rate", "vat_amount", "line_total",
        ]


class POSTransactionSerializer(serializers.ModelSerializer):
    lines = POSTransactionLineSerializer(many=True)

    class Meta:
        model = POSTransaction
        fields = [
            "id", "transaction_number", "session", "payment_method",
            "subtotal", "discount", "vat_amount", "total_amount",
            "amount_paid", "change_due", "transacted_at",
            "zatca_invoice", "created_offline", "synced_at",
            "lines",
        ]
        read_only_fields = ["id", "transaction_number", "zatca_invoice", "synced_at"]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        txn = POSTransaction.objects.create(**validated_data)
        for line_data in lines_data:
            POSTransactionLine.objects.create(transaction=txn, **line_data)
        return txn


class POSSessionSerializer(serializers.ModelSerializer):
    terminal_name = serializers.CharField(source="terminal.terminal_id", read_only=True)
    cashier_name = serializers.CharField(source="cashier.get_full_name", read_only=True)

    class Meta:
        model = POSSession
        fields = [
            "id", "terminal", "terminal_name", "cashier", "cashier_name",
            "opened_at", "closed_at", "status",
            "opening_cash", "closing_cash",
            "total_sales", "total_vat", "total_cash", "total_mada",
            "total_stc_pay", "total_credit_card", "transaction_count",
        ]
        read_only_fields = [
            "id", "cashier", "cashier_name", "opened_at", "closed_at",
            "total_sales", "total_vat", "total_cash",
            "total_mada", "total_stc_pay", "total_credit_card", "transaction_count",
        ]
