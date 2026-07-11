"""
Alert message formatters — builds Telegram HTML messages from Alert objects.
Professional layout without emojis, symbols, or AI/trust branding.
Uses native Telegram HTML tags (blockquote, bold, anchor) for structural card layouts.
"""
from html import escape
from core.utils import format_date_nigerian


def format_alert_full(alert) -> str:
    """
    Full alert message for direct delivery to users.
    Professional card layout using Telegram's native blockquote tag.
    """
    agency_display = f"<b>{escape(alert.agency.name)} ({escape(alert.agency.acronym)})</b>"
    event_display = f"<i>{escape(alert.get_event_type_display())}</i>"
    
    # Format positions as a clean list
    positions_str = alert.positions or ""
    if positions_str:
        parts = [p.strip() for p in positions_str.replace(';', ',').split(',') if p.strip()]
        if parts:
            positions_formatted = "\n" + "\n".join(f"- {escape(p)}" for p in parts)
        else:
            positions_formatted = f"\n- {escape(positions_str)}"
    else:
        positions_formatted = "\n- Not specified"
        
    # Format requirements
    reqs_str = alert.requirements or ""
    if reqs_str:
        reqs_formatted = f"\n\nRequirements:\n{escape(reqs_str)}"
    else:
        reqs_formatted = ""

    deadline_val = escape(str(alert.deadline)) if alert.deadline else 'Open'
    
    return (
        f"{agency_display}\n"
        f"{event_display}\n"
        f"<blockquote>"
        f"<b>Positions:</b>{positions_formatted}"
        f"{reqs_formatted}\n\n"
        f"<b>Deadline:</b> {deadline_val}\n"
        f"<b>Portal:</b> <a href='{escape(alert.source_url)}'>{escape(alert.source_url)}</a>"
        f"</blockquote>"
    )


def format_alert_brief(alert) -> str:
    """
    Structured summary of an alert for list views (/jobs, /search).
    Groups fields into a distinct bordered card using blockquotes.
    """
    agency_display = f"<b>{escape(alert.agency.name)} ({escape(alert.agency.acronym)})</b>"
    event_display = f"<i>{escape(alert.get_event_type_display())}</i>"
    
    # Format positions as a clean list
    positions_str = alert.positions or ""
    if positions_str:
        parts = [p.strip() for p in positions_str.replace(';', ',').split(',') if p.strip()]
        if parts:
            positions_formatted = "\n" + "\n".join(f"- {escape(p)}" for p in parts)
        else:
            positions_formatted = f"\n- {escape(positions_str)}"
    else:
        positions_formatted = "\n- Not specified"

    deadline_val = escape(str(alert.deadline)) if alert.deadline else 'Open'
    
    return (
        f"{agency_display}\n"
        f"{event_display}\n"
        f"<blockquote>"
        f"<b>Positions:</b>{positions_formatted}\n\n"
        f"<b>Deadline:</b> {deadline_val}\n"
        f"<b>Portal:</b> <a href='{escape(alert.source_url)}'>{escape(alert.source_url)}</a>"
        f"</blockquote>"
    )


def format_alert_unconfirmed(alert) -> str:
    """
    Alert message for unconfirmed openings.
    """
    agency_display = f"<b>{escape(alert.agency.name)} ({escape(alert.agency.acronym)})</b>"
    event_display = f"<i>{escape(alert.get_event_type_display())} (Unconfirmed)</i>"
    
    positions_str = alert.positions or ""
    if positions_str:
        parts = [p.strip() for p in positions_str.replace(';', ',').split(',') if p.strip()]
        if parts:
            positions_formatted = "\n" + "\n".join(f"- {escape(p)}" for p in parts)
        else:
            positions_formatted = f"\n- {escape(positions_str)}"
    else:
        positions_formatted = "\n- Not specified"

    deadline_val = escape(str(alert.deadline)) if alert.deadline else 'Open'
    
    return (
        f"{agency_display}\n"
        f"{event_display}\n"
        f"<blockquote>"
        f"<b>Positions:</b>{positions_formatted}\n\n"
        f"<b>Deadline:</b> {deadline_val}\n\n"
        f"Note: This update has not been officially verified. Please confirm details directly on the official website of {escape(alert.agency.name)} before applying.\n\n"
        f"<b>Portal:</b> <a href='{escape(alert.source_url)}'>{escape(alert.source_url)}</a>"
        f"</blockquote>"
    )


def format_portal_status_change(agency_acronym: str, new_status: str, timestamp: str) -> str:
    """Portal status change alert template without emojis."""
    return (
        f"<b>Portal Status Update</b>\n\n"
        f"Agency: {escape(agency_acronym)}\n"
        f"New Status: {escape(new_status.upper())}\n"
        f"Time: {escape(timestamp)}"
    )


def format_deadline_extension(alert, old_deadline: str, new_deadline: str) -> str:
    """Deadline extension alert template without emojis."""
    agency_display = f"<b>{escape(alert.agency.name)} ({escape(alert.agency.acronym)})</b>"
    
    positions_str = alert.positions or ""
    if positions_str:
        parts = [p.strip() for p in positions_str.replace(';', ',').split(',') if p.strip()]
        if parts:
            positions_formatted = "\n" + "\n".join(f"- {escape(p)}" for p in parts)
        else:
            positions_formatted = f"\n- {escape(positions_str)}"
    else:
        positions_formatted = "\n- Not specified"

    return (
        f"{agency_display}\n"
        f"<blockquote>"
        f"<b>Status: Deadline Extended</b>\n\n"
        f"<b>Positions:</b>{positions_formatted}\n\n"
        f"Old Deadline: {escape(str(old_deadline))}\n"
        f"New Deadline: {escape(str(new_deadline))}\n\n"
        f"<b>Portal:</b> <a href='{escape(alert.source_url)}'>{escape(alert.source_url)}</a>"
        f"</blockquote>"
    )
