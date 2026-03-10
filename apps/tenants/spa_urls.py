import os
from pathlib import Path
from django.urls import re_path
from django.http import HttpResponse, FileResponse
from django.conf import settings


SPA_DIR = Path(settings.BASE_DIR) / "static" / "spa"


def spa_index(request, path=""):
    """
    Serve React SPA index.html for all /app/* routes.
    Falls back gracefully if build doesn't exist yet.
    """
    index = SPA_DIR / "index.html"
    if index.exists():
        return FileResponse(open(index, "rb"), content_type="text/html")
    return HttpResponse(
        """<!DOCTYPE html><html lang="ar" dir="rtl">
        <head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
        <title>ERP System</title>
        <style>body{font-family:'Segoe UI',sans-serif;background:#0f172a;display:flex;align-items:center;
        justify-content:center;height:100vh;margin:0;}.box{text-align:center;color:white;}
        h1{font-size:1.5rem;}p{color:#94a3b8;font-size:.875rem;}
        code{background:#1e293b;padding:8px 16px;border-radius:8px;display:inline-block;
        margin-top:12px;font-size:.8rem;color:#38bdf8;}</style></head>
        <body><div class="box"><h1>🏗️ Frontend Not Built Yet</h1>
        <p>Run the React build to serve the SPA:</p>
        <code>cd frontend && npm install && npm run build</code></div></body></html>""",
        content_type="text/html",
        status=200,
    )


urlpatterns = [
    re_path(r"^.*$", spa_index),
]
