"""
Inventory models for Saudi AI-ERP.
Products, Warehouses, Stock Levels, Stock Movements, Categories, Reorder Alerts.
"""
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ProductCategory(models.Model):
    """Product categories for organization."""
    name_ar = models.CharField("اسم التصنيف (عربي)", max_length=100)
    name_en = models.CharField("Category Name", max_length=100)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "تصنيف المنتجات"
        verbose_name_plural = "تصنيفات المنتجات"

    def __str__(self):
        return self.name_ar


class Product(models.Model):
    """Product / Item master."""
    class ProductType(models.TextChoices):
        GOODS = "goods", "بضاعة — Goods"
        SERVICE = "service", "خدمة — Service"
        CONSUMABLE = "consumable", "مواد استهلاكية — Consumable"

    sku = models.CharField("رمز المنتج (SKU)", max_length=50, unique=True)
    barcode = models.CharField("الباركود", max_length=50, blank=True)
    name_ar = models.CharField("اسم المنتج (عربي)", max_length=255)
    name_en = models.CharField("Product Name (English)", max_length=255)
    description_ar = models.TextField("الوصف (عربي)", blank=True)
    description_en = models.TextField("Description", blank=True)

    category = models.ForeignKey(ProductCategory, null=True, blank=True, on_delete=models.SET_NULL)
    product_type = models.CharField(max_length=15, choices=ProductType.choices, default=ProductType.GOODS)

    # Pricing
    cost_price = models.DecimalField("سعر التكلفة", max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField("سعر البيع", max_digits=12, decimal_places=2, default=0)
    vat_inclusive = models.BooleanField("السعر شامل الضريبة", default=False)

    # Units
    unit = models.CharField("وحدة القياس", max_length=20, default="EA", choices=[
        ("EA", "قطعة — Each"),
        ("KG", "كيلوغرام — Kilogram"),
        ("LTR", "لتر — Liter"),
        ("MTR", "متر — Meter"),
        ("BOX", "صندوق — Box"),
        ("PKG", "عبوة — Package"),
        ("SET", "طقم — Set"),
        ("HR", "ساعة — Hour"),
    ])

    # Stock control
    is_trackable = models.BooleanField("تتبع المخزون", default=True)
    reorder_level = models.DecimalField("حد إعادة الطلب", max_digits=12, decimal_places=2, default=0)
    reorder_quantity = models.DecimalField("كمية إعادة الطلب", max_digits=12, decimal_places=2, default=0)
    min_stock = models.DecimalField("الحد الأدنى", max_digits=12, decimal_places=2, default=0)
    max_stock = models.DecimalField("الحد الأقصى", max_digits=12, decimal_places=2, default=0)

    # GL Account
    revenue_account_code = models.CharField("حساب الإيراد", max_length=10, default="4100")
    cogs_account_code = models.CharField("حساب تكلفة البضاعة", max_length=10, default="5100")
    inventory_account_code = models.CharField("حساب المخزون", max_length=10, default="1140")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"
        ordering = ["name_ar"]

    def __str__(self):
        return f"{self.sku} — {self.name_ar}"

    @property
    def profit_margin(self):
        if self.selling_price > 0:
            return round((self.selling_price - self.cost_price) / self.selling_price * 100, 2)
        return 0


class Warehouse(models.Model):
    """Physical storage locations."""
    code = models.CharField("رمز المستودع", max_length=20, unique=True)
    name_ar = models.CharField("اسم المستودع (عربي)", max_length=100)
    name_en = models.CharField("Warehouse Name", max_length=100)
    city = models.CharField("المدينة", max_length=50, default="الرياض")
    address = models.TextField("العنوان", blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField("مستودع افتراضي", default=False)

    class Meta:
        verbose_name = "مستودع"
        verbose_name_plural = "المستودعات"

    def __str__(self):
        return f"{self.code} — {self.name_ar}"


class StockLevel(models.Model):
    """Current stock quantity per product per warehouse."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_levels")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stock_levels")
    quantity = models.DecimalField("الكمية الحالية", max_digits=12, decimal_places=2, default=0)
    reserved = models.DecimalField("الكمية المحجوزة", max_digits=12, decimal_places=2, default=0)
    last_counted_at = models.DateTimeField("آخر جرد", null=True, blank=True)

    class Meta:
        verbose_name = "مستوى المخزون"
        unique_together = [("product", "warehouse")]

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.code}: {self.quantity}"

    @property
    def available(self):
        return self.quantity - self.reserved

    @property
    def needs_reorder(self):
        return self.quantity <= self.product.reorder_level


class StockMovement(models.Model):
    """Track all stock ins and outs."""
    class MovementType(models.TextChoices):
        RECEIVE = "receive", "استلام — Receive"
        ISSUE = "issue", "صرف — Issue"
        TRANSFER = "transfer", "تحويل — Transfer"
        ADJUSTMENT = "adjustment", "تسوية — Adjustment"
        RETURN = "return", "مرتجع — Return"
        POS_SALE = "pos_sale", "بيع نقطة بيع — POS Sale"

    movement_number = models.CharField("رقم الحركة", max_length=50, unique=True)
    movement_type = models.CharField(max_length=15, choices=MovementType.choices)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="movements")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="movements")
    to_warehouse = models.ForeignKey(Warehouse, null=True, blank=True, on_delete=models.SET_NULL, related_name="incoming_movements")

    quantity = models.DecimalField("الكمية", max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField("تكلفة الوحدة", max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField("التكلفة الإجمالية", max_digits=18, decimal_places=2, default=0)

    reference = models.CharField("المرجع", max_length=100, blank=True)
    notes = models.TextField("ملاحظات", blank=True)

    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "حركة مخزون"
        verbose_name_plural = "حركات المخزون"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_number} — {self.product.sku} ({self.movement_type})"
