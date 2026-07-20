"""
All bot message string constants.
Keeps message text out of handler logic for easy editing/translation.
"""

WELCOME_MESSAGE = """
<b>Welcome to RecruitmentAlert, {name}.</b>

This service will notify you as soon as any Nigerian government agency opens a new recruitment portal.

You are subscribed to receive alerts for over 30 agencies, including:
- NNPC, NCS, EFCC, CBN, FIRS
- NPF, NSCDC, DSS, NIS, NAF
- NAFDAC, JAMB, FAAN, NCAA, and more

All openings are verified directly against official sources.

<b>Commands:</b>
/jobs - Latest openings
/agencies - All monitored agencies
/history - Your alert history
/search - Search by keyword
/status - Portal health status
/settings - Your preferences
/help - Full command list
"""

RETURNING_MESSAGE = """
<b>Welcome back to RecruitmentAlert, {name}.</b>

Your subscriptions are active. You will receive notifications as soon as new job postings are detected.

<b>Quick Commands:</b>
/jobs - View latest jobs
/status - Check portal statuses
/settings - Manage your preferences
"""

CONSENT_MESSAGE = """
<b>Data Privacy Notice</b>

To provide this service, RecruitmentAlert stores the following information:
- Your Telegram ID and name
- Your subscription preferences

This is handled in accordance with the Nigeria Data Protection Regulation (NDPR).

Your data will not be shared with third parties. You can delete your profile and subscriptions at any time using the /delete command.

Select 'I Agree' to proceed.
"""

HELP_MESSAGE = """
<b>RecruitmentAlert - Command List</b>

/start - Register and subscribe to all agencies
/jobs - Latest 10 job openings
/latest - Most recent alert
/agencies - All monitored agencies and portal status
/history - Your last 20 received alerts
/search [keyword] - Search alerts by keyword
/status - Portal health summary
/settings - Your notification preferences
/unsubscribe - Stop receiving alerts
/report - Report a suspicious alert
/help - Show this message

RecruitmentAlert monitors official Nigerian government agency portals for updates.
"""

UNSUBSCRIBED_MESSAGE = """
<b>You have been unsubscribed.</b>

You will no longer receive recruitment alerts. To re-subscribe, send the /start command.
"""

ERROR_MESSAGE = "An error occurred. Please try again or type /help."

PORTAL_DOWN_MESSAGE = """
<b>{agency_acronym} Portal Offline</b>

The recruitment portal for {agency_name} appears to be temporarily offline. We will continue monitoring and notify you once it becomes available.
"""

USER_BANNED_MESSAGE = "Your account has been suspended. Please contact support."
