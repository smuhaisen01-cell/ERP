"""Inventory serializers."""
from rest_framework import serializers
from .models import ProductCategory, Product, Warehouse, StockLevel, StockMovement


class ProductCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ["id", "name_ar", "name_en", "parent", "is_active", "product_count"]

    def get_product_count(self, obj):
        return obj.product_set.filter(is_active=True).count()


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name_en", read_only=True, default="")
    total_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "sku", "barcode", "name_ar", "name_en",
            "category", "category_name", "product_type",
            "cost_price", "selling_price", "unit",
            "is_trackable", "reorder_level", "is_active",
            "total_stock",
        ]

    def get_total_stock(self, obj):
        agg = obj.stock_levels.aggregate(total=serializers.models.Sum("quantity"))
        return str(agg["total"] or 0)


class ProductSerializer(serializers.ModelSerializer):
    profit_margin = serializers.FloatField(read_only=True)
    stock_levels = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "sku", "barcode", "name_ar", "name_en",
            "description_ar", "description_en",
            "category", "product_type",
            "cost_price", "selling_price", "vat_inclusive", "unit",
            "is_trackable", "reorder_level", "reorder_quantity",
            "min_stock", "max_stock",
            "revenue_account_code", "cogs_account_code", "inventory_account_code",
            "is_active", "profit_margin", "stock_levels",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_stock_levels(self, obj):
        return [
            {
                "warehouse": sl.warehouse.name_en,
                "warehouse_code": sl.warehouse.code,
                "quantity": str(sl.quantity),
                "reserved": str(sl.reserved),
                "available": str(sl.available),
                "needs_reorder": sl.needs_reorder,
            }
            for sl in obj.stock_levels.select_related("warehouse").all()
        ]


class WarehouseSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = [
            "id", "code", "name_ar", "name_en", "city", "address",
            "is_active", "is_default", "product_count", "total_value",
        ]

    def get_product_count(self, obj):
        return obj.stock_levels.filter(quantity__gt=0).count()

    def get_total_value(self, obj):
        total = 0
        for sl in obj.stock_levels.select_related("product").filter(quantity__gt=0):
            total += sl.quantity * sl.product.cost_price
        return str(total)


class StockLevelSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name_en", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name_en", read_only=True)
    available = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    needs_reorder = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockLevel
        fields = [
            "id", "product", "product_sku", "product_name",
            "warehouse", "warehouse_name",
            "quantity", "reserved", "available", "needs_reorder",
            "last_counted_at",
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name_en", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name_en", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "movement_number", "movement_type",
            "product", "product_sku", "product_name",
            "warehouse", "warehouse_name", "to_warehouse",
            "quantity", "unit_cost", "total_cost",
            "reference", "notes",
            "created_by", "created_at",
        ]
        read_only_fields = ["id", "movement_number", "total_cost", "created_by", "created_at"]
