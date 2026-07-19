"""
Telegram Webhook View — receives incoming updates from Telegram.
Validates the secret token, parses the Update, and dispatches to handlers.
"""
import json
import logging
import hashlib
import hmac

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(View):
    """
    POST /telegram/webhook/
    Accepts Telegram Update objects. Validates webhook secret header.
    In production, Nginx additionally restricts to Telegram IP ranges.
    """

    def post(self, request, *args, **kwargs):
        # ── Validate webhook secret ───────────────────────────────────────────
        secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
        expected = settings.TELEGRAM_WEBHOOK_SECRET

        # Fail hard if secret is not configured — an empty secret would allow
        # any caller to bypass validation and inject fake Telegram updates.
        if not expected or not hmac.compare_digest(secret, expected):
            logger.warning("Rejected webhook request: invalid or missing secret token.")
            return HttpResponse(status=403)

        # ── Parse the Update ──────────────────────────────────────────────────
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Webhook received invalid JSON body.")
            return HttpResponse(status=400)

        # ── Dispatch to handler (async via Celery in production) ──────────────
        try:
            from .dispatcher import dispatch_update
            dispatch_update(data)
        except Exception as exc:
            logger.exception(f"Error dispatching Telegram update: {exc}")
            # Always return 200 to Telegram to prevent retries
            return JsonResponse({'ok': True})

        return JsonResponse({'ok': True})

    def get(self, request, *args, **kwargs):
        """Health check endpoint."""
        return JsonResponse({'status': 'GovAlert webhook active'})
