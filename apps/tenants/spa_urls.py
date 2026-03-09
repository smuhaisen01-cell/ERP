from django.urls import re_path
from django.http import HttpResponse

def spa_index(request, path=""):
    return HttpResponse("<h1>ERP SPA — Connect React build here</h1>")

urlpatterns = [
    re_path(r"^.*$", spa_index),
]
