"""
Django Channels WebSocket consumer — Live AI Dashboard.
Compliance note: this consumer NEVER opens a Postgres connection.
All data served from Redis KPI cache only.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger("apps.ai")


class AIDashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket endpoint: wss://app.yourdomain.sa/ws/ai/dashboard/
    Each tenant has its own channel group: dashboard:{schema_name}

    COMPLIANCE: Zero database connections in this consumer.
    All data read from Redis KPI cache (kpi:{tenant_id}).
    AI Platform pushes updates via channel_layer.group_send().
    """

    async def connect(self):
        # Tenant is set by TenantMainMiddleware on the scope
        self.tenant = self.scope.get("tenant")
        if not self.tenant:
            await self.close(code=4003)
            return

        self.tenant_id = self.tenant.schema_name
        self.group_name = f"dashboard:{self.tenant_id}"

        # Join tenant's dashboard channel group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info(f"Dashboard WS connected: tenant={self.tenant_id} channel={self.channel_name}")

        # Send current KPI snapshot immediately on connect (from Redis, not DB)
        snapshot = await self._get_kpi_snapshot()
        await self.send(text_data=json.dumps({
            "type": "kpi_snapshot",
            "data": snapshot,
            "tenant": self.tenant_id,
        }))

        # Send recent alerts
        alerts = await self._get_recent_alerts(limit=10)
        await self.send(text_data=json.dumps({
            "type": "alerts_snapshot",
            "alerts": alerts,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"Dashboard WS disconnected: tenant={getattr(self, 'tenant_id', '?')} code={close_code}")

    async def receive(self, text_data):
        """
        Handle client messages.
        Currently only supports requesting specific metric refreshes.
        Client cannot write data through WebSocket.
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get("type") == "refresh_metric":
            metric = data.get("metric")
            if metric:
                value = await self._get_single_kpi(metric)
                await self.send(text_data=json.dumps({
                    "type": "kpi_update",
                    "metric": metric,
                    "value": value,
                    "delta": None,
                }))

    # ─── Channel layer handlers (called by AI Platform) ───────────────────

    async def kpi_update(self, event):
        """
        Called by channel_layer.group_send() from AI Platform event consumer.
        Pushes a single KPI diff to the browser.
        """
        await self.send(text_data=json.dumps({
            "type": "kpi_update",
            "metric": event["metric"],
            "value": event["value"],
            "delta": event.get("delta"),
            "alert": event.get("alert"),      # Arabic alert text if anomaly
            "severity": event.get("severity", "info"),
        }))

    async def ai_alert(self, event):
        """Called when AI Platform triggers a new alert."""
        await self.send(text_data=json.dumps({
            "type": "ai_alert",
            "alert_id": event["alert_id"],
            "message_ar": event["message_ar"],
            "message_en": event["message_en"],
            "severity": event["severity"],   # info | warning | critical
            "metadata": event.get("metadata", {}),
        }))

    async def forecast_update(self, event):
        """Called when AI Platform updates a forecast."""
        await self.send(text_data=json.dumps({
            "type": "forecast_update",
            "forecast_type": event["forecast_type"],  # demand | cashflow | vat
            "data": event["data"],
        }))

    # ─── Redis helpers (no DB) ────────────────────────────────────────────

    async def _get_kpi_snapshot(self) -> dict:
        """Read all KPIs from Redis hash — no Postgres connection."""
        from django_redis import get_redis_connection
        r = get_redis_connection("default")
        raw = r.hgetall(f"kpi:{self.tenant_id}")
        if not raw:
            return self._default_kpis()
        return {k.decode(): v.decode() for k, v in raw.items()}

    async def _get_single_kpi(self, metric: str) -> str | None:
        from django_redis import get_redis_connection
        r = get_redis_connection("default")
        val = r.hget(f"kpi:{self.tenant_id}", metric)
        return val.decode() if val else None

    async def _get_recent_alerts(self, limit: int = 10) -> list:
        """Read recent AI alerts from Redis list."""
        from django_redis import get_redis_connection
        r = get_redis_connection("default")
        raw = r.lrange(f"alerts:{self.tenant_id}", 0, limit - 1)
        alerts = []
        for item in raw:
            try:
                alerts.append(json.loads(item.decode()))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        return alerts

    def _default_kpis(self) -> dict:
        """Return zero-value KPIs for a fresh tenant."""
        return {
            "revenue_today_sar": "0",
            "revenue_mtd_sar": "0",
            "vat_collected_today": "0",
            "invoices_today": "0",
            "open_ar_sar": "0",
            "stock_alert_count": "0",
            "anomaly_alert_count": "0",
            "cashflow_7day_forecast": "0",
        }
