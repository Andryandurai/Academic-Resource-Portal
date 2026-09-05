from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("webhook/", views.webhook, name="whatsapp-webhook"),
    path("dev/simulate/", views.dev_simulate, name="whatsapp-dev-simulate"),
    path("dev/outbox/", views.dev_outbox, name="whatsapp-dev-outbox"),
]
