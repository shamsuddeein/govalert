"""
Alert message formatters — builds Telegram HTML messages from Alert objects.
"""
from core.utils import build_trust_badge, format_date_nigerian


def format_alert_full(alert) -> str:
    """
    Full alert message for direct delivery to users.
    Used by the notification dispatcher for high-trust alerts.
    """
    trust_badge = build_trust_badge(alert.trust_score)
    positions = f"\n📋 <b>Positions:</b> {alert.positions}" if alert.positions else ''
    deadline = f"\n⏰ <b>Deadline:</b> {alert.deadline}" if alert.deadline else ''
    requirements = f"\n📝 <b>Requirements:</b> {alert.requirements[:200]}" if alert.requirements else ''

    return (
        f"🔔 <b>{alert.agency.acronym} — {alert.get_event_type_display()}</b>\n\n"
        f"{alert.title}"
        f"{positions}"
        f"{deadline}"
        f"{requirements}\n\n"
        f"🔗 <a href='{alert.source_url}'>Apply on Official Portal</a>\n\n"
        f"🛡️ Trust: {trust_badge} ({alert.trust_score}/100)\n"
        f"📅 {format_date_nigerian(alert.created_at)}"
    )


def format_alert_brief(alert) -> str:
    """
    One-line summary of an alert for list views (/jobs, /history, /search).
    """
    deadline = f" — Deadline: {alert.deadline}" if alert.deadline else ''
    return f"• <b>{alert.agency.acronym}</b>: {alert.title}{deadline}"


def format_alert_unconfirmed(alert) -> str:
    """
    Alert message for medium-trust openings (score 50–69).
    Includes strong warning to verify at the official site.
    """
    return (
        f"⚠️ <b>[UNCONFIRMED] {alert.agency.acronym} — {alert.get_event_type_display()}</b>\n\n"
        f"{alert.title}\n\n"
        f"🔗 <a href='{alert.source_url}'>View posting</a>\n\n"
        f"⚠️ <b>WARNING:</b> This alert could not be fully verified. "
        f"Always confirm at the official <b>{alert.agency.name}</b> website before applying.\n\n"
        f"🛡️ Trust Score: {alert.trust_score}/100"
    )


def format_portal_status_change(agency_acronym: str, new_status: str, timestamp: str) -> str:
    """Portal status change alert template."""
    return (
        f"📉 <b>PORTAL STATUS CHANGE</b>\n\n"
        f"🏢 <b>Agency:</b> {agency_acronym}\n"
        f"📊 <b>Change:</b> Portal went {new_status.upper()}\n"
        f"🕐 <b>Detected:</b> {timestamp}\n\n"
        f"↩️ We will notify you when it comes back online."
    )


def format_deadline_extension(alert, old_deadline: str, new_deadline: str) -> str:
    """Deadline extension alert template."""
    positions = f"\n📋 <b>Positions:</b> {alert.positions}" if alert.positions else ''
    return (
        f"📅 <b>DEADLINE EXTENDED</b>\n\n"
        f"🏢 <b>Agency:</b> {alert.agency.acronym}\n"
        f"{positions}\n"
        f"🔴 <b>Old Deadline:</b> {old_deadline}\n"
        f"✅ <b>New Deadline:</b> {new_deadline}\n\n"
        f"🔗 <a href='{alert.source_url}'>Apply on Official Portal</a>"
    )
