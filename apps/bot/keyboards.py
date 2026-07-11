"""
InlineKeyboardMarkup builders for all bot interactions.
"""
import json


def _build_keyboard(buttons: list[list[dict]]) -> dict:
    """Build a Telegram InlineKeyboardMarkup dict."""
    return {
        'inline_keyboard': [
            [{'text': b['text'], 'callback_data': b['data']} for b in row]
            for row in buttons
        ]
    }


def get_consent_keyboard() -> dict:
    return _build_keyboard([
        [{'text': '✅ I Agree', 'data': 'consent_agree'}],
    ])


def get_main_menu_keyboard() -> dict:
    return _build_keyboard([
        [{'text': '📋 Browse Jobs', 'data': 'show_jobs'}, {'text': '🏛️ Agencies', 'data': 'show_agencies'}],
        [{'text': '📜 My History', 'data': 'show_history'}, {'text': '⚙️ Settings', 'data': 'show_settings'}],
    ])


def get_alert_keyboard(alert_id: int) -> dict:
    return _build_keyboard([
        [
            {'text': '💾 Save', 'data': f'save_alert:{alert_id}'},
            {'text': '⚠️ Report Fake', 'data': f'report_alert:{alert_id}'},
            {'text': '📤 Share', 'data': f'share_alert:{alert_id}'},
        ]
    ])


def get_settings_keyboard() -> dict:
    return _build_keyboard([
        [{'text': '🔔 Toggle Alerts On/Off', 'data': 'settings_toggle_alerts'}],
        [{'text': '🌍 Change Timezone', 'data': 'settings_timezone'}],
        [{'text': '🗑️ Delete My Data', 'data': 'settings_delete_data'}],
    ])


def get_onboarding_keyboard() -> dict:
    return _build_keyboard([
        [
            {'text': '⚙️ Customize Alerts', 'data': 'show_settings'},
            {'text': '✅ Done', 'data': 'onboarding_done'}
        ]
    ])


def get_report_reason_keyboard(alert_id: int) -> dict:
    return _build_keyboard([
        [{'text': '💰 Asked me to pay', 'data': f'report_reason:{alert_id}:PAYMENT'}],
        [{'text': '🌐 Wrong website', 'data': f'report_reason:{alert_id}:WRONG_URL'}],
        [{'text': '🏛️ Not from official source', 'data': f'report_reason:{alert_id}:NOT_OFFICIAL'}],
        [{'text': '🚨 Content looks suspicious', 'data': f'report_reason:{alert_id}:SUSPICIOUS'}],
        [{'text': '❓ Other', 'data': f'report_reason:{alert_id}:OTHER'}],
    ])


def get_unsubscribe_confirm_keyboard() -> dict:
    return _build_keyboard([
        [
            {'text': '✅ Yes, unsubscribe', 'data': 'unsubscribe_confirm'},
            {'text': '❌ Cancel', 'data': 'unsubscribe_cancel'},
        ]
    ])
