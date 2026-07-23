import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail
from apps.accounts.models import TelegramUser, WebUser, UserState
from apps.subscriptions.models import KeywordSubscription
from apps.notifications.sender import send_message
from apps.alerts.models import Alert
from apps.bot.templates import format_alert_full

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send a custom broadcast or alert notification to all subscribers across Telegram and Email."

    def add_arguments(self, parser):
        parser.add_argument('--text', type=str, help='Broadcast message text to send')
        parser.add_argument('--subject', type=str, default='📢 RecruitmentAlert Announcement', help='Email subject line')
        parser.add_argument('--alert-id', type=int, help='Alert ID to dispatch to all subscribers')

    def handle(self, *args, **options):
        alert_id = options.get('alert_id')
        text = options.get('text')
        subject = options.get('subject')

        if alert_id:
            try:
                alert = Alert.objects.get(pk=alert_id)
                from apps.notifications.tasks import dispatch_alert
                dispatch_alert(alert.id)
                self.stdout.write(self.style.SUCCESS(f"Successfully triggered dispatch for Alert #{alert_id} ({alert.title})."))
                return
            except Alert.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Alert #{alert_id} not found."))
                return

        if not text:
            self.stderr.write(self.style.ERROR("Please provide either --text 'Your message' or --alert-id ID."))
            return

        self.stdout.write(f"Starting broadcast to all subscribers...")

        # 1. Telegram Subscribers
        telegram_users = TelegramUser.objects.filter(state=UserState.ACTIVE, receive_alerts=True)
        tg_success = 0
        formatted_tg_text = f"📢 <b>Broadcast Announcement</b>\n\n{text}\n\n<i>— RecruitmentAlert Team</i>"
        for user in telegram_users:
            try:
                res = send_message(chat_id=user.telegram_id, text=formatted_tg_text, parse_mode='HTML')
                if res:
                    tg_success += 1
            except Exception as exc:
                logger.warning(f"Failed to send broadcast to TG user {user.telegram_id}: {exc}")

        # 2. Email Subscribers
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'alerts@recruitmentalert.com.ng')
        web_users = WebUser.objects.filter(user__is_active=True).exclude(user__email='').select_related('user')
        email_recipients = set()
        for wu in web_users:
            if wu.user.email:
                email_recipients.add(wu.user.email)

        kw_subs = KeywordSubscription.objects.filter(is_active=True)
        for ks in kw_subs:
            if ks.email:
                email_recipients.add(ks.email)

        email_success = 0
        for email in email_recipients:
            try:
                send_mail(
                    subject=subject,
                    message=f"Hello,\n\n{text}\n\n— RecruitmentAlert Intelligence Team\nhttps://www.recruitmentalert.com.ng",
                    from_email=from_email,
                    recipient_list=[email],
                    fail_silently=True,
                )
                email_success += 1
            except Exception as exc:
                logger.warning(f"Failed to send broadcast email to {email}: {exc}")

        self.stdout.write(self.style.SUCCESS(
            f"Broadcast delivered successfully!\n"
            f"• Telegram Telegram Bot Subscribers: {tg_success}\n"
            f"• Email Subscribers: {email_success}\n"
            f"• Total Messages Delivered: {tg_success + email_success}"
        ))
