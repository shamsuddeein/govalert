"""
All bot message string constants.
Keeps message text out of handler logic for easy editing/translation.
"""

WELCOME_MESSAGE = """
<b>Welcome to RecruitmentAlert, {name}.</b>

This service notifies you instantly when Nigerian government agencies open recruitment portals.

You are set to receive verified alerts for monitored federal MDAs (NNPC, NCS, EFCC, Police, Immigration, FIRS, etc.).

<b>🔒 Privacy Notice (NDPR & NDPA 2023):</b>
When you use this bot, we store your Telegram user ID to send you alerts. We do NOT share your data with anyone. Type <b>/stop</b> at any time to delete your data and unsubscribe. Read our Privacy Policy: https://www.recruitmentalert.com.ng/privacy

<b>Commands:</b>
/jobs - Latest openings
/agencies - Monitored agency statuses
/stop - Delete data & unsubscribe
/help - Command list
"""

RETURNING_MESSAGE = """
<b>Welcome back to RecruitmentAlert, {name}.</b>

Your subscriptions are active. You will receive notifications as soon as new job postings are detected.

<b>Quick Commands:</b>
/jobs - View latest jobs
/status - Check portal statuses
/stop - Delete data & unsubscribe
"""

CONSENT_MESSAGE = """
<b>Data Privacy Notice</b>

To provide this service, RecruitmentAlert stores your Telegram ID, name, and subscription preferences.

This data is processed in accordance with the Nigeria Data Protection Regulation (NDPR) and NDPA 2023.

Your data will never be sold or shared. You can delete your profile and subscriptions instantly at any time using the <b>/stop</b> command.
"""

HELP_MESSAGE = """
<b>RecruitmentAlert : Command List</b>

/start - Register & activate alerts
/jobs - View latest verified job openings
/agencies - Monitored agencies & portal health
/status - System status summary
/stop - Delete your data & unsubscribe
/help - Show this message

<b>Data Rights:</b>
Type /stop anytime to delete all your personal data from our database instantly. Privacy Policy: https://www.recruitmentalert.com.ng/privacy
"""

UNSUBSCRIBED_MESSAGE = """
<b>You have been unsubscribed.</b>

Your Telegram alert preferences and profile data have been permanently deleted from our database in compliance with NDPR. You will no longer receive alerts.

To re-subscribe at any time, send /start.
"""

ERROR_MESSAGE = "An error occurred. Please try again or type /help."

PORTAL_DOWN_MESSAGE = """
<b>{agency_acronym} Portal Offline</b>

The recruitment portal for {agency_name} appears to be temporarily offline. We will continue monitoring and notify you once it becomes available.
"""

USER_BANNED_MESSAGE = "Your account has been suspended. Please contact support."
