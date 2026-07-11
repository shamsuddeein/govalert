"""
Alert message formatters — builds Telegram HTML messages from Alert objects.
"""
from html import escape
from core.utils import build_trust_badge, format_date_nigerian


def format_alert_full(alert) -> str:
    """
    Full alert message for direct delivery to users.
    Used by the notification dispatcher for high-trust alerts.
    Escapes all user-generated text to prevent HTML injection issues.
    """
    trust_badge = build_trust_badge(alert.trust_score)
    
    # Escape all user-generated text to prevent HTML parsing errors
    title = escape(alert.title) if alert.title else ''
    positions = f"\n📋 <b>Positions:</b> {escape(alert.positions)}" if alert.positions else ''
    deadline = f"\n⏰ <b>Deadline:</b> {escape(str(alert.deadline))}" if alert.deadline else ''
    requirements_text = escape(alert.requirements[:200]) if alert.requirements else ''
    requirements = f"\n📝 <b>Requirements:</b> {requirements_text}" if alert.requirements else ''
    source_url = escape(alert.source_url) if alert.source_url else ''

    return (
        f"🔔 <b>{escape(alert.agency.acronym)} — {alert.get_event_type_display()}</b>\n\n"
        f"{title}"
        f"{positions}"
        f"{deadline}"
        f"{requirements}\n\n"
        f"🔗 <a href='{source_url}'>Apply on Official Portal</a>\n\n"
        f"🛡️ Trust: {trust_badge} ({alert.trust_score}/100)\n"
        f"📅 {format_date_nigerian(alert.created_at)}"
    )


def format_alert_brief(alert) -> str:
    """
    One-line summary of an alert for list views (/jobs, /history, /search).
    """
    deadline = f" — Deadline: {escape(str(alert.deadline))}" if alert.deadline else ''
    return f"• <b>{escape(alert.agency.acronym)}</b>: {escape(alert.title)}{deadline}"


def format_alert_unconfirmed(alert) -> str:
    """
    Alert message for medium-trust openings (score 50–69).
    Includes strong warning to verify at the official site.
    """
    agency_acronym = escape(alert.agency.acronym)
    agency_name = escape(alert.agency.name)
    title = escape(alert.title) if alert.title else ''
    source_url = escape(alert.source_url) if alert.source_url else ''
    return (
        f"⚠️ <b>[UNCONFIRMED] {agency_acronym} — {alert.get_event_type_display()}</b>\n\n"
        f"{title}\n\n"
        f"🔗 <a href='{source_url}'>View posting</a>\n\n"
        f"⚠️ <b>WARNING:</b> This alert could not be fully verified. "
        f"Always confirm at the official <b>{agency_name}</b> website before applying.\n\n"
        f"🛡️ Trust Score: {alert.trust_score}/100"
    )


def format_portal_status_change(agency_acronym: str, new_status: str, timestamp: str) -> str:
    """Portal status change alert template."""
    return (
        f"📉 <b>PORTAL STATUS CHANGE</b>\n\n"
        f"🏢 <b>Agency:</b> {escape(agency_acronym)}\n"
        f"📊 <b>Change:</b> Portal went {escape(new_status.upper())}\n"
        f"🕐 <b>Detected:</b> {escape(timestamp)}\n\n"
        f"↩️ We will notify you when it comes back online."
    )


def format_deadline_extension(alert, old_deadline: str, new_deadline: str) -> str:
    """Deadline extension alert template."""
    positions = f"\n📋 <b>Positions:</b> {escape(alert.positions)}" if alert.positions else ''
    agency_acronym = escape(alert.agency.acronym)
    old_deadline_text = escape(str(old_deadline))
    new_deadline_text = escape(str(new_deadline))
    source_url = escape(alert.source_url) if alert.source_url else ''
    return (
        f"📅 <b>DEADLINE EXTENDED</b>\n\n"
        f"🏢 <b>Agency:</b> {agency_acronym}\n"
        f"{positions}\n"
        f"🔴 <b>Old Deadline:</b> {old_deadline_text}\n"
        f"✅ <b>New Deadline:</b> {new_deadline_text}\n\n"
        f"🔗 <a href='{source_url}'>Apply on Official Portal</a>"
    )
