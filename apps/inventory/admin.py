from django.contrib import admin
from .models import ProductCategory, Product, Warehouse, StockLevel, StockMovement

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name_ar", "name_en", "parent", "is_active"]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["sku", "name_ar", "category", "product_type", "cost_price", "selling_price", "is_active"]
    list_filter = ["product_type", "category", "is_active"]
    search_fields = ["sku", "barcode", "name_ar", "name_en"]

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["code", "name_ar", "city", "is_active", "is_default"]

@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ["product", "warehouse", "quantity", "reserved"]
    list_filter = ["warehouse"]

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["movement_number", "movement_type", "product", "warehouse", "quantity", "created_at"]
    list_filter = ["movement_type", "warehouse"]
