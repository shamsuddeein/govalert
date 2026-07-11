from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Register bot commands with Telegram via the setMyCommands API."

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not token or token == 'MOCK_BOT_TOKEN':
            self.stdout.write(self.style.ERROR("TELEGRAM_BOT_TOKEN is not configured or is using mock value."))
            return

        commands = [
            {"command": "start", "description": "Start the bot and setup preferences"},
            {"command": "help", "description": "View usage guide and commands list"},
            {"command": "jobs", "description": "List current active job openings"},
            {"command": "search", "description": "Search job openings by keyword"},
            {"command": "agencies", "description": "View monitored government agencies"},
            {"command": "status", "description": "Check portal system health status"},
            {"command": "settings", "description": "Manage subscription preferences"},
            {"command": "latest", "description": "Show the single latest job alert details"},
            {"command": "history", "description": "View past/expired job openings"},
            {"command": "report", "description": "Report a fake portal or scam alert"},
            {"command": "unsubscribe", "description": "Stop receiving all notifications"}
        ]

        url = f"https://api.telegram.org/bot{token}/setMyCommands"
        try:
            response = requests.post(url, json={"commands": commands}, timeout=10)
            result = response.json()
            if result.get("ok"):
                self.stdout.write(self.style.SUCCESS("Successfully registered bot commands menu with Telegram!"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to register commands: {result.get('description')}"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"API request failed: {exc}"))
