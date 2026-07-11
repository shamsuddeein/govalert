"""
Bot app URLs — Telegram webhook endpoint.
"""
from django.urls import path
from .webhook import TelegramWebhookView

app_name = 'bot'

urlpatterns = [
    path('webhook/', TelegramWebhookView.as_view(), name='webhook'),
]
