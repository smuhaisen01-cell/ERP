"""
AI API views — Copilot chat, dashboard Q&A, alerts, forecasting, auto-categorization.
All AI operations are READ-ONLY — enforced by read-only DB role + code constraints.
"""
import json
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse

from .services.llm_client import LLMClientFactory, COPILOT_SYSTEM_PROMPT
from .services.data_context import get_financial_context, get_alert_context, get_forecast_data

logger = logging.getLogger("apps.ai")


class CopilotChatView(APIView):
    """
    AI Copilot — natural language chat about ERP data.
    POST /api/ai/chat/
    Body: { "message": "What are my top sales this month?", "history": [...] }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_message = request.data.get("message", "").strip()
        history = request.data.get("history", [])
        stream = request.data.get("stream", False)

        if not user_message:
            return Response({"error": "message is required"}, status=400)

        # Build context with live data
        financial_ctx, _ = get_financial_context()
        system = COPILOT_SYSTEM_PROMPT + "\n\n" + financial_ctx

        # Build message history
        messages = []
        for h in history[-10:]:  # Keep last 10 messages
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        try:
            llm = LLMClientFactory.get()

            if stream:
                def generate():
                    for token in llm.stream(system, messages, max_tokens=2048):
                        yield f"data: {json.dumps({'token': token})}\n\n"
                    yield "data: [DONE]\n\n"

                return StreamingHttpResponse(generate(), content_type="text/event-stream")
            else:
                response = llm.complete(system, messages, max_tokens=2048)
                return Response({
                    "response": response,
                    "context_used": True,
                })

        except Exception as e:
            logger.error(f"AI Copilot error: {e}")
            return Response({
                "response": f"AI service unavailable: {str(e)}. Please check that ANTHROPIC_API_KEY is configured.",
                "context_used": False,
                "error": True,
            })


class DashboardQAView(APIView):
    """
    Dashboard Q&A — quick questions about business data.
    POST /api/ai/dashboard-qa/
    Body: { "question": "How many invoices this month?" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get("question", "").strip()
        if not question:
            return Response({"error": "question is required"}, status=400)

        financial_ctx, raw_data = get_financial_context()

        system = """You are a concise business analyst for a Saudi ERP system.
Answer the question using ONLY the data provided. Be brief (1-3 sentences).
Use numbers and SAR amounts. If the data doesn't contain the answer, say so.
Respond in the same language as the question."""

        messages = [{"role": "user", "content": f"DATA:\n{financial_ctx}\n\nQUESTION: {question}"}]

        try:
            llm = LLMClientFactory.get()
            answer = llm.complete(system, messages, max_tokens=500)
            return Response({"answer": answer, "data": raw_data})
        except Exception as e:
            return Response({"answer": f"AI unavailable: {e}", "error": True})


class SmartAlertsView(APIView):
    """
    Smart Alerts — anomaly detection and compliance warnings.
    GET /api/ai/alerts/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        alerts = get_alert_context()

        # Optionally enrich with AI analysis
        enrich = request.query_params.get("enrich", "false") == "true"
        if enrich and alerts:
            try:
                llm = LLMClientFactory.get()
                alert_text = "\n".join([a['message_en'] for a in alerts])
                system = "You are a Saudi ERP compliance advisor. Given these alerts, provide brief actionable recommendations (2-3 sentences max per alert). Respond in English."
                messages = [{"role": "user", "content": f"ALERTS:\n{alert_text}\n\nProvide recommendations:"}]
                advice = llm.complete(system, messages, max_tokens=500)

                for alert in alerts:
                    alert['ai_recommendation'] = advice
            except Exception:
                pass

        return Response({
            "alerts": alerts,
            "count": len(alerts),
            "severity_counts": {
                "high": sum(1 for a in alerts if a['severity'] == 'high'),
                "medium": sum(1 for a in alerts if a['severity'] == 'medium'),
                "low": sum(1 for a in alerts if a['severity'] == 'low'),
            }
        })


class ForecastView(APIView):
    """
    Revenue Forecasting — uses historical data + AI for predictions.
    GET /api/ai/forecast/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        monthly_data = get_forecast_data()

        if len(monthly_data) < 2:
            return Response({
                "forecast": None,
                "message": "Not enough data for forecasting (need at least 2 months)",
                "historical": monthly_data,
            })

        # Simple trend calculation
        revenues = [float(m['revenue']) for m in monthly_data]
        if len(revenues) >= 2:
            avg_growth = sum(revenues[i] - revenues[i-1] for i in range(1, len(revenues))) / (len(revenues) - 1)
            last_revenue = revenues[-1]
            forecast_3m = [round(last_revenue + avg_growth * (i+1), 2) for i in range(3)]
        else:
            forecast_3m = []

        # AI-enhanced forecast
        ai_analysis = None
        try:
            llm = LLMClientFactory.get()
            data_str = json.dumps(monthly_data, indent=2)
            system = """You are a financial forecasting expert for Saudi SMEs. 
Analyze the revenue trend and provide:
1. Trend direction (growing/declining/stable)
2. 3-month forecast with confidence level
3. One actionable recommendation
Be concise (5 sentences max). Use SAR amounts."""
            messages = [{"role": "user", "content": f"Monthly revenue data:\n{data_str}"}]
            ai_analysis = llm.complete(system, messages, max_tokens=500)
        except Exception:
            pass

        return Response({
            "historical": monthly_data,
            "simple_forecast_3m": forecast_3m,
            "avg_monthly_growth": round(avg_growth, 2) if len(revenues) >= 2 else 0,
            "ai_analysis": ai_analysis,
        })


class AutoCategorizeView(APIView):
    """
    Auto-categorize expenses — suggest GL accounts.
    POST /api/ai/categorize/
    Body: { "description": "Office supplies from Jarir", "amount": 500 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        description = request.data.get("description", "")
        amount = request.data.get("amount", 0)

        if not description:
            return Response({"error": "description is required"}, status=400)

        # Get chart of accounts for context
        from apps.accounting.models import ChartOfAccount
        accounts = ChartOfAccount.objects.filter(
            is_leaf=True, is_active=True, account_type='expense'
        ).values('code', 'name_en', 'name_ar')[:50]

        accounts_str = "\n".join([f"{a['code']} - {a['name_en']} ({a['name_ar']})" for a in accounts])

        system = """You are an accounting assistant for a Saudi company using SOCPA Chart of Accounts.
Given a transaction description and amount, suggest the best GL account from the provided chart.
Respond ONLY in JSON format: {"account_code": "XXXX", "account_name": "...", "confidence": 0.0-1.0, "reason": "..."}"""

        messages = [{"role": "user", "content": f"""
Expense accounts:
{accounts_str}

Transaction: "{description}" — {amount} SAR

Suggest the best account:"""}]

        try:
            llm = LLMClientFactory.get()
            response = llm.complete(system, messages, max_tokens=200)

            # Try to parse JSON
            try:
                # Clean response
                clean = response.strip()
                if clean.startswith("```"):
                    clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
                result = json.loads(clean)
                return Response(result)
            except json.JSONDecodeError:
                return Response({"suggestion": response, "parsed": False})

        except Exception as e:
            return Response({"error": f"AI unavailable: {e}"}, status=503)


class AIStatusView(APIView):
    """Check AI service status and configuration."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.conf import settings

        backend = getattr(settings, 'AI_BACKEND', 'not_configured')
        has_key = bool(getattr(settings, 'ANTHROPIC_API_KEY', ''))

        status = "ready" if has_key else "no_api_key"

        # Test connection
        if has_key:
            try:
                llm = LLMClientFactory.get()
                llm.complete("Test", [{"role": "user", "content": "Hi"}], max_tokens=5)
                status = "connected"
            except Exception as e:
                status = f"error: {e}"

        return Response({
            "backend": backend,
            "status": status,
            "has_api_key": has_key,
            "model": getattr(settings, 'ANTHROPIC_MODEL', 'not_set'),
        })
