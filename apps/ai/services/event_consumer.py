"""
Redis Stream event consumer — AI Platform.
Reads ERP domain events from Redis Streams.
Updates KPI cache, runs anomaly detection, pushes to live dashboard.
COMPLIANCE: Never writes to Postgres ERP schemas.
           All output goes to: Redis KPI cache, Redis alert list, channel_layer.
"""
import json
import logging
import uuid
from datetime import datetime, timezone as tz
from typing import Any

import redis as redis_lib
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings

logger = logging.getLogger("apps.ai")


class ERPEventConsumer:
    """
    Consumes events from: erp_events:{tenant_schema}
    Consumer group: ai_platform_consumers
    Each AI service is a separate consumer in the group.

    Run via Celery task or management command:
      python manage.py consume_erp_events
    """

    CONSUMER_GROUP = "ai_platform_consumers"
    CONSUMER_NAME = "ai_consumer_1"
    BLOCK_MS = 5000   # Block for 5s waiting for new events

    # Map event_type → handler method
    HANDLERS = {
        "invoice.created":        "handle_invoice_created",
        "invoice.zatca_cleared":  "handle_invoice_cleared",
        "invoice.zatca_reported": "handle_invoice_cleared",
        "gl.entry_posted":        "handle_gl_entry",
        "payment.received":       "handle_payment",
        "stock.level_changed":    "handle_stock_change",
        "pos.sale":               "handle_pos_sale",
        "pos.session_closed":     "handle_pos_session_closed",
    }

    def __init__(self):
        self.redis = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
        self.channel_layer = get_channel_layer()

    def run_forever(self, tenant_schemas: list[str]):
        """Main loop — runs as long-lived Celery worker."""
        stream_keys = {
            f"{settings.REDIS_STREAM_PREFIX}:{schema}": ">"
            for schema in tenant_schemas
        }
        self._ensure_consumer_groups(list(stream_keys.keys()))

        logger.info(f"AI event consumer started: watching {len(stream_keys)} tenant streams")

        while True:
            try:
                results = self.redis.xreadgroup(
                    groupname=self.CONSUMER_GROUP,
                    consumername=self.CONSUMER_NAME,
                    streams=stream_keys,
                    count=50,
                    block=self.BLOCK_MS,
                )
                if not results:
                    continue

                for stream_key, messages in results:
                    tenant_schema = stream_key.split(":")[-1]  # t_{vat_number}
                    for msg_id, fields in messages:
                        self._process_message(tenant_schema, msg_id, fields)

            except Exception as e:
                logger.error(f"Event consumer error: {e}", exc_info=True)

    def _process_message(self, tenant_schema: str, msg_id: str, fields: dict):
        try:
            event = json.loads(fields.get("payload", "{}"))
            event_type = fields.get("event_type", "")
            payload = json.loads(fields.get("payload", "{}")) if isinstance(fields.get("payload"), str) else {}

            handler_name = self.HANDLERS.get(event_type)
            if handler_name:
                handler = getattr(self, handler_name)
                handler(tenant_schema, payload)
            else:
                logger.debug(f"No handler for event_type={event_type}")

            # Acknowledge message
            stream_key = f"{settings.REDIS_STREAM_PREFIX}:{tenant_schema}"
            self.redis.xack(stream_key, self.CONSUMER_GROUP, msg_id)

        except Exception as e:
            logger.error(f"Error processing event {msg_id}: {e}", exc_info=True)

    # ─── Event Handlers ────────────────────────────────────────────────────

    def handle_invoice_created(self, tenant_schema: str, payload: dict):
        """
        New invoice created in ERP Core.
        → Update invoice count KPI
        → Run anomaly check
        → Update cash flow model
        """
        total = float(payload.get("total_amount", 0))
        vat = float(payload.get("vat_amount", 0))

        # 1. Update KPI cache
        pipe = self.redis.pipeline()
        pipe.hincrbyfloat(f"kpi:{tenant_schema}", "revenue_today_sar", total)
        pipe.hincrbyfloat(f"kpi:{tenant_schema}", "vat_collected_today", vat)
        pipe.hincrby(f"kpi:{tenant_schema}", "invoices_today", 1)
        pipe.execute()

        # 2. Anomaly check
        score = self._compute_anomaly_score(tenant_schema, "invoice", payload)
        alert = None
        if score > settings.AI_ANOMALY_THRESHOLD:
            inv_num = payload.get("invoice_number", "?")
            alert = self._dispatch_alert(
                tenant_schema,
                alert_type="invoice_anomaly",
                message_ar=f"⚠️ فاتورة مشبوهة: {inv_num} (نقاط الشذوذ: {score:.2f})",
                message_en=f"⚠️ Suspicious invoice: {inv_num} (anomaly score: {score:.2f})",
                severity="warning",
                metadata={"invoice_number": inv_num, "anomaly_score": score},
            )

        # 3. Push to live dashboard
        self._push_kpi_update(tenant_schema, "revenue_today_sar", total, alert)
        self._push_kpi_update(tenant_schema, "vat_collected_today", vat)

    def handle_invoice_cleared(self, tenant_schema: str, payload: dict):
        """B2B invoice cleared by ZATCA → update revenue KPIs."""
        total = float(payload.get("total_amount", 0))
        self._push_kpi_update(tenant_schema, "revenue_today_sar", total)

    def handle_gl_entry(self, tenant_schema: str, payload: dict):
        """GL entry posted → anomaly check, zakat base update."""
        score = self._compute_anomaly_score(tenant_schema, "gl_entry", payload)
        if score > settings.AI_ANOMALY_THRESHOLD:
            self._dispatch_alert(
                tenant_schema,
                alert_type="gl_anomaly",
                message_ar=f"🔍 قيد يومية غير معتاد: {payload.get('entry_number', '?')}",
                message_en=f"🔍 Unusual GL entry: {payload.get('entry_number', '?')}",
                severity="warning",
                metadata={"anomaly_score": score, **payload},
            )

        self.redis.hincrby(f"kpi:{tenant_schema}", "gl_entries_today", 1)

    def handle_payment(self, tenant_schema: str, payload: dict):
        """Payment received → cash flow update."""
        amount = float(payload.get("amount", 0))
        self.redis.hincrbyfloat(f"kpi:{tenant_schema}", "payments_received_today", amount)
        self._push_kpi_update(tenant_schema, "payments_received_today", amount)

    def handle_stock_change(self, tenant_schema: str, payload: dict):
        """Stock level changed — check if below reorder point."""
        if payload.get("below_reorder"):
            product = payload.get("product_name_ar", "منتج")
            days_to_stockout = payload.get("days_to_stockout", "?")

            self.redis.hincrby(f"kpi:{tenant_schema}", "stock_alert_count", 1)
            alert = self._dispatch_alert(
                tenant_schema,
                alert_type="low_stock",
                message_ar=f"⚠️ مخزون منخفض: {product} — {days_to_stockout} أيام حتى النفاد",
                message_en=f"⚠️ Low stock: {product} — {days_to_stockout} days to stockout",
                severity="warning",
                metadata=payload,
            )
            self._push_kpi_update(tenant_schema, "stock_alert_count", 1, alert)

    def handle_pos_sale(self, tenant_schema: str, payload: dict):
        """POS sale completed → update POS KPIs."""
        total = float(payload.get("total_amount", 0))
        pipe = self.redis.pipeline()
        pipe.hincrbyfloat(f"kpi:{tenant_schema}", "pos_sales_today", total)
        pipe.hincrby(f"kpi:{tenant_schema}", "pos_transactions_today", 1)
        pipe.execute()

    def handle_pos_session_closed(self, tenant_schema: str, payload: dict):
        """POS session closed → compare actual vs forecast."""
        actual = float(payload.get("session_total", 0))
        branch = payload.get("branch_code", "")
        # Trigger async forecast comparison task
        from apps.ai.tasks import compare_pos_vs_forecast
        compare_pos_vs_forecast.delay(tenant_schema, branch, actual)

    # ─── Anomaly Detection ─────────────────────────────────────────────────

    def _compute_anomaly_score(self, tenant_schema: str, event_type: str, payload: dict) -> float:
        """
        Simple rule-based anomaly scoring.
        In production: use trained Isolation Forest model per tenant.
        """
        score = 0.0
        amount = float(payload.get("total_amount", payload.get("amount", 0)))

        # Round number check (common in fraudulent invoices)
        if amount > 0 and amount == int(amount) and amount >= 10000:
            score += 0.3

        # Unusual hour (outside 06:00–22:00 Riyadh time)
        hour = datetime.now(tz=tz.utc).hour + 3  # UTC+3
        if hour < 6 or hour > 22:
            score += 0.2

        # Very large amount
        if amount > 500000:
            score += 0.2

        # First-time large amount (no history in cache)
        max_seen = self.redis.hget(f"kpi:{tenant_schema}", "max_invoice_amount")
        if max_seen is None and amount > 50000:
            score += 0.2

        return min(score, 1.0)

    # ─── Alert Dispatcher ─────────────────────────────────────────────────

    def _dispatch_alert(
        self, tenant_schema: str, alert_type: str,
        message_ar: str, message_en: str,
        severity: str, metadata: dict
    ) -> dict:
        """Create alert, store in Redis, push to dashboard."""
        alert = {
            "id": str(uuid.uuid4()),
            "type": alert_type,
            "message_ar": message_ar,
            "message_en": message_en,
            "severity": severity,
            "tenant_id": tenant_schema,
            "created_at": datetime.now(tz=tz.utc).isoformat(),
            "metadata": metadata,
        }

        # Store in Redis alert list (TTL handled by maxmemory-policy)
        self.redis.lpush(f"alerts:{tenant_schema}", json.dumps(alert))
        self.redis.ltrim(f"alerts:{tenant_schema}", 0, 499)  # Keep last 500

        # Update anomaly count KPI
        self.redis.hincrby(f"kpi:{tenant_schema}", "anomaly_alert_count", 1)

        # Push to live dashboard
        async_to_sync(self.channel_layer.group_send)(
            f"dashboard:{tenant_schema}",
            {
                "type": "ai_alert",
                "alert_id": alert["id"],
                "message_ar": message_ar,
                "message_en": message_en,
                "severity": severity,
                "metadata": metadata,
            }
        )

        return alert

    # ─── Dashboard Push ───────────────────────────────────────────────────

    def _push_kpi_update(
        self, tenant_schema: str, metric: str, delta: float, alert: dict | None = None
    ):
        """Push a single KPI update to all connected dashboard clients."""
        value = self.redis.hget(f"kpi:{tenant_schema}", metric)

        async_to_sync(self.channel_layer.group_send)(
            f"dashboard:{tenant_schema}",
            {
                "type": "kpi_update",
                "metric": metric,
                "value": value or "0",
                "delta": delta,
                "alert": alert,
            }
        )

    # ─── Consumer Group Setup ─────────────────────────────────────────────

    def _ensure_consumer_groups(self, stream_keys: list[str]):
        for key in stream_keys:
            try:
                self.redis.xgroup_create(key, self.CONSUMER_GROUP, id="0", mkstream=True)
            except redis_lib.exceptions.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
