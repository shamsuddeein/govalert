"""
Inline keyboard callback handlers.
Handles button presses: Save, Report Fake, Consent, Settings toggles.
"""
import logging

logger = logging.getLogger(__name__)


def handle_callback(callback_query: dict):
    """Route a callback_query to the correct sub-handler."""
    data: str = callback_query.get('data', '')
    user_data = callback_query.get('from', {})
    chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
    message_id = callback_query.get('message', {}).get('message_id')

    logger.debug(f"Callback: {data} from user {user_data.get('id')}")

    if data == 'consent_agree':
        _handle_consent_agree(callback_query)
    elif data.startswith('save_alert:'):
        _handle_save_alert(callback_query, alert_id=int(data.split(':')[1]))
    elif data.startswith('report_alert:'):
        _handle_report_start(callback_query, alert_id=int(data.split(':')[1]))
    elif data.startswith('report_reason:'):
        _handle_report_reason(callback_query, data)
    elif data == 'settings_toggle_alerts':
        _handle_toggle_alerts(callback_query)
    elif data == 'unsubscribe_confirm':
        _handle_unsubscribe_confirm(callback_query)
    else:
        logger.warning(f"Unknown callback data: {data}")


def _handle_consent_agree(callback_query: dict):
    """User tapped [I Agree] on the NDPR consent message."""
    from apps.accounts.models import TelegramUser
    from apps.subscriptions.services import auto_subscribe_all
    from apps.notifications.sender import send_message, answer_callback_query
    from apps.bot.messages import WELCOME_MESSAGE

    user_data = callback_query.get('from', {})
    chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
    telegram_id = user_data.get('id')

    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        user.give_consent()
        auto_subscribe_all(user)
        user.state = 'ACTIVE'
        user.save(update_fields=['state'])
        answer_callback_query(callback_query['id'], text="✅ Welcome to GovAlert!")
        send_message(chat_id=chat_id, text=WELCOME_MESSAGE.format(name=user.display_name), parse_mode='HTML')
    except TelegramUser.DoesNotExist:
        logger.error(f"Consent callback from unknown user {telegram_id}")


def _handle_save_alert(callback_query: dict, alert_id: int):
    from apps.accounts.models import TelegramUser
    from apps.alerts.models import Alert, AlertAction, AlertActionType
    from apps.notifications.sender import answer_callback_query

    telegram_id = callback_query.get('from', {}).get('id')
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        alert = Alert.objects.get(pk=alert_id)
        AlertAction.objects.get_or_create(
            user=user, alert=alert,
            defaults={'action_type': AlertActionType.SAVED}
        )
        answer_callback_query(callback_query['id'], text="✅ Alert saved to your history.")
    except (TelegramUser.DoesNotExist, Alert.DoesNotExist):
        answer_callback_query(callback_query['id'], text="⚠️ Could not save alert.")


def _handle_report_start(callback_query: dict, alert_id: int):
    """Show report reason keyboard."""
    from apps.notifications.sender import send_message, answer_callback_query
    from apps.bot.keyboards import get_report_reason_keyboard
    chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
    answer_callback_query(callback_query['id'])
    send_message(
        chat_id=chat_id,
        text="⚠️ <b>Why do you think this is fake?</b>",
        parse_mode='HTML',
        reply_markup=get_report_reason_keyboard(alert_id),
    )


def _handle_report_reason(callback_query: dict, data: str):
    """Store user's report reason."""
    from apps.accounts.models import TelegramUser
    from apps.alerts.models import Alert
    from apps.detector.models import AlertReport
    from apps.notifications.sender import answer_callback_query

    # data format: "report_reason:{alert_id}:{reason}"
    parts = data.split(':')
    if len(parts) < 3:
        return
    alert_id, reason = int(parts[1]), parts[2]

    telegram_id = callback_query.get('from', {}).get('id')
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        alert = Alert.objects.get(pk=alert_id)
        AlertReport.objects.get_or_create(
            alert=alert, user=user,
            defaults={'reason': reason}
        )
        # Check if 3+ reports — trigger admin escalation
        report_count = AlertReport.objects.filter(alert=alert).count()
        alert.report_count = report_count
        alert.save(update_fields=['report_count'])
        if report_count >= 3:
            _escalate_to_admin(alert)
        answer_callback_query(callback_query['id'], text="✅ Report submitted. Thank you.")
    except (TelegramUser.DoesNotExist, Alert.DoesNotExist):
        answer_callback_query(callback_query['id'], text="⚠️ Could not submit report.")


def _handle_toggle_alerts(callback_query: dict):
    from apps.accounts.models import TelegramUser
    from apps.notifications.sender import answer_callback_query
    telegram_id = callback_query.get('from', {}).get('id')
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        user.receive_alerts = not user.receive_alerts
        user.save(update_fields=['receive_alerts'])
        status = "enabled" if user.receive_alerts else "disabled"
        answer_callback_query(callback_query['id'], text=f"🔔 Alerts {status}.")
    except TelegramUser.DoesNotExist:
        pass


def _handle_unsubscribe_confirm(callback_query: dict):
    from apps.accounts.models import TelegramUser
    from apps.subscriptions.services import unsubscribe_all
    from apps.notifications.sender import answer_callback_query, send_message
    from apps.bot.messages import UNSUBSCRIBED_MESSAGE
    telegram_id = callback_query.get('from', {}).get('id')
    chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        unsubscribe_all(user)
        answer_callback_query(callback_query['id'])
        send_message(chat_id=chat_id, text=UNSUBSCRIBED_MESSAGE)
    except TelegramUser.DoesNotExist:
        pass


def _escalate_to_admin(alert):
    """Notify admins when 3+ users report the same alert."""
    from apps.accounts.models import TelegramUser
    from apps.notifications.sender import send_message
    admins = TelegramUser.objects.filter(is_admin=True, state='ACTIVE')
    text = (
        f"🚨 <b>URGENT: Alert Flagged by 3+ Users</b>\n\n"
        f"Alert ID: #{alert.pk}\n"
        f"Agency: {alert.agency.acronym}\n"
        f"Title: {alert.title}\n"
        f"Reports: {alert.report_count}\n\n"
        f"Please review at /admin"
    )
    for admin in admins:
        try:
            send_message(chat_id=admin.telegram_id, text=text, parse_mode='HTML')
        except Exception as exc:
            logger.error(f"Could not notify admin {admin.telegram_id}: {exc}")
