"""
Inventory API viewsets.
Products, Warehouses, Stock Levels, Stock Movements.
"""
import uuid
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ProductCategory, Product, Warehouse, StockLevel, StockMovement
from .serializers import (
    ProductCategorySerializer, ProductSerializer, ProductListSerializer,
    WarehouseSerializer, StockLevelSerializer, StockMovementSerializer,
)


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    search_fields = ["name_ar", "name_en"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    filterset_fields = ["category", "product_type", "is_active", "is_trackable"]
    search_fields = ["sku", "barcode", "name_ar", "name_en"]
    ordering_fields = ["name_ar", "selling_price", "created_at"]
    ordering = ["name_ar"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductSerializer

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """Products below reorder level."""
        alerts = []
        for sl in StockLevel.objects.select_related("product", "warehouse").filter(
            product__is_active=True, product__is_trackable=True
        ):
            if sl.needs_reorder:
                alerts.append({
                    "product_sku": sl.product.sku,
                    "product_name": sl.product.name_en,
                    "warehouse": sl.warehouse.name_en,
                    "current_qty": str(sl.quantity),
                    "reorder_level": str(sl.product.reorder_level),
                    "reorder_qty": str(sl.product.reorder_quantity),
                })
        return Response({"alerts": alerts, "count": len(alerts)})

    @action(detail=False, methods=["get"])
    def valuation(self, request):
        """Total inventory valuation."""
        products = Product.objects.filter(is_active=True, is_trackable=True)
        total_cost = Decimal("0")
        total_retail = Decimal("0")
        items = []

        for p in products:
            total_qty = p.stock_levels.aggregate(q=Sum("quantity"))["q"] or Decimal("0")
            if total_qty > 0:
                cost_val = total_qty * p.cost_price
                retail_val = total_qty * p.selling_price
                total_cost += cost_val
                total_retail += retail_val
                items.append({
                    "sku": p.sku, "name": p.name_en,
                    "quantity": str(total_qty),
                    "cost_value": str(cost_val),
                    "retail_value": str(retail_val),
                })

        return Response({
            "total_cost_value": str(total_cost),
            "total_retail_value": str(total_retail),
            "potential_profit": str(total_retail - total_cost),
            "product_count": len(items),
            "items": items,
        })


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    search_fields = ["code", "name_ar", "name_en", "city"]

    @action(detail=False, methods=["post"])
    def setup_default(self, request):
        """Create a default warehouse if none exist."""
        wh = Warehouse.objects.first()
        if not wh:
            wh = Warehouse.objects.create(
                code="WH-MAIN", name_ar="المستودع الرئيسي",
                name_en="Main Warehouse", city="Riyadh", is_default=True,
            )
        return Response(WarehouseSerializer(wh).data)


class StockLevelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockLevel.objects.select_related("product", "warehouse").all()
    serializer_class = StockLevelSerializer
    filterset_fields = ["product", "warehouse"]


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("product", "warehouse").all()
    serializer_class = StockMovementSerializer
    filterset_fields = ["movement_type", "product", "warehouse"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        mvn = f"MOV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        movement = serializer.save(
            movement_number=mvn,
            created_by=self.request.user,
            total_cost=serializer.validated_data.get("quantity", 0) * serializer.validated_data.get("unit_cost", 0),
        )
        self._update_stock(movement)

    def _update_stock(self, movement):
        """Update stock levels based on movement type."""
        with transaction.atomic():
            sl, _ = StockLevel.objects.get_or_create(
                product=movement.product,
                warehouse=movement.warehouse,
                defaults={"quantity": 0, "reserved": 0},
            )

            if movement.movement_type in ("receive", "return"):
                sl.quantity += movement.quantity
            elif movement.movement_type in ("issue", "pos_sale"):
                sl.quantity -= movement.quantity
            elif movement.movement_type == "adjustment":
                sl.quantity = movement.quantity  # Set to exact amount
            elif movement.movement_type == "transfer" and movement.to_warehouse:
                sl.quantity -= movement.quantity
                sl.save()
                # Add to destination
                dest_sl, _ = StockLevel.objects.get_or_create(
                    product=movement.product,
                    warehouse=movement.to_warehouse,
                    defaults={"quantity": 0, "reserved": 0},
                )
                dest_sl.quantity += movement.quantity
                dest_sl.save()
                return

            sl.save()

    @action(detail=False, methods=["post"])
    def receive(self, request):
        """Quick receive stock — simplified endpoint."""
        product_id = request.data.get("product")
        warehouse_id = request.data.get("warehouse")
        quantity = Decimal(str(request.data.get("quantity", 0)))
        unit_cost = Decimal(str(request.data.get("unit_cost", 0)))

        if not all([product_id, warehouse_id, quantity > 0]):
            return Response({"error": "product, warehouse, quantity required"}, status=400)

        mvn = f"RCV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        movement = StockMovement.objects.create(
            movement_number=mvn,
            movement_type="receive",
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=quantity * unit_cost,
            reference=request.data.get("reference", ""),
            notes=request.data.get("notes", ""),
            created_by=request.user,
        )
        self._update_stock(movement)

        return Response(StockMovementSerializer(movement).data, status=201)

    @action(detail=False, methods=["post"])
    def transfer(self, request):
        """Quick transfer between warehouses."""
        product_id = request.data.get("product")
        from_wh = request.data.get("warehouse")
        to_wh = request.data.get("to_warehouse")
        quantity = Decimal(str(request.data.get("quantity", 0)))

        if not all([product_id, from_wh, to_wh, quantity > 0]):
            return Response({"error": "product, warehouse, to_warehouse, quantity required"}, status=400)

        # Check available stock
        sl = StockLevel.objects.filter(product_id=product_id, warehouse_id=from_wh).first()
        if not sl or sl.available < quantity:
            return Response({"error": "Insufficient stock"}, status=400)

        mvn = f"TRF-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        movement = StockMovement.objects.create(
            movement_number=mvn,
            movement_type="transfer",
            product_id=product_id,
            warehouse_id=from_wh,
            to_warehouse_id=to_wh,
            quantity=quantity,
            reference=request.data.get("reference", ""),
            notes=request.data.get("notes", ""),
            created_by=request.user,
        )
        self._update_stock(movement)

        return Response(StockMovementSerializer(movement).data, status=201)
