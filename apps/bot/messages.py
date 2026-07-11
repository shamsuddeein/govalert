"""
All bot message string constants.
Keeps message text out of handler logic for easy editing/translation.
"""

WELCOME_MESSAGE = """
🇳🇬 <b>Welcome to GovAlert, {name}!</b>

I'll alert you the moment any Nigerian government agency opens a new recruitment portal.

You're now subscribed to <b>30+ agencies</b> including:
• NNPC, NCS, EFCC, CBN, FIRS
• NPF, NSCDC, DSS, NIS, NAF
• NAFDAC, JAMB, FAAN, NCAA, and more

<b>No fake alerts.</b> Every opening is verified with our trust scoring system + AI.

<b>Commands:</b>
/jobs — Latest openings
/agencies — All monitored agencies
/history — Your alert history
/search — Search by keyword
/status — Portal health status
/settings — Your preferences
/help — Full command list
"""

RETURNING_MESSAGE = """
🇳🇬 <b>Welcome back to GovAlert, {name}!</b>

Your subscriptions are active. You will receive alerts as soon as new job postings are detected.

<b>Quick Commands:</b>
/jobs — View latest jobs
/status — Check portal statuses
/settings — Manage your preferences
"""

CONSENT_MESSAGE = """
🔒 <b>Data Privacy Notice</b>

Before you start, GovAlert needs to store a small amount of data to function:

• Your Telegram ID and name
• Your subscription preferences

This is in line with Nigeria's NDPR data protection law.

We will <b>never</b> share your data with third parties.
You can delete your data at any time with /delete.

Tap <b>I Agree</b> to continue.
"""

HELP_MESSAGE = """
📖 <b>GovAlert — Command List</b>

/start — Register and subscribe to all agencies
/jobs — Latest 10 job openings
/latest — Most recent alert
/agencies — All monitored agencies + portal status
/history — Your last 20 received alerts
/search [keyword] — Search alerts by keyword
/status — Portal health summary
/settings — Your notification preferences
/unsubscribe — Stop receiving alerts
/report — Report a suspicious alert
/help — This message

<i>GovAlert monitors 30+ Nigerian government agency portals every 15 minutes.</i>
"""

UNSUBSCRIBED_MESSAGE = """
✅ <b>You have been unsubscribed.</b>

You will no longer receive recruitment alerts.

To re-subscribe to all agencies, simply send /start again.
"""

ERROR_MESSAGE = "⚠️ Something went wrong. Please try again or type /help."

PORTAL_DOWN_MESSAGE = """
⚠️ <b>{agency_acronym} Portal Temporarily Unavailable</b>

The {agency_name} recruitment portal appears to be offline.
We're monitoring it and will alert you as soon as it's back.
"""

USER_BANNED_MESSAGE = "🚫 Your account has been suspended. Contact support if you believe this is an error."
