from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Register the Telegram webhook URL with Telegram."

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        url = getattr(settings, 'TELEGRAM_WEBHOOK_URL', None)
        secret = getattr(settings, 'TELEGRAM_WEBHOOK_SECRET', None)

        if not token or token == 'MOCK_BOT_TOKEN':
            self.stdout.write(self.style.ERROR("TELEGRAM_BOT_TOKEN is not configured or using mock value."))
            return
        if not url:
            self.stdout.write(self.style.ERROR("TELEGRAM_WEBHOOK_URL is not configured."))
            return

        api_url = f"https://api.telegram.org/bot{token}/setWebhook"
        payload = {
            "url": url,
        }
        if secret:
            payload["secret_token"] = secret

        self.stdout.write(f"Registering webhook to {url}...")
        try:
            response = requests.post(api_url, json=payload, timeout=10)
            result = response.json()
            if result.get("ok"):
                self.stdout.write(self.style.SUCCESS("Successfully set webhook with Telegram!"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to set webhook: {result.get('description')}"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"API request failed: {exc}"))
