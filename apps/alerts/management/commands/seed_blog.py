from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.alerts.models import BlogPost

TECH_ARTICLE_BODY = """Building real-time notification infrastructure is essential for modern web applications. At RecruitmentAlert, when an official Nigerian government portal opens a verified recruitment drive, thousands of subscribers receive instant alerts on their smartphones via our automated Telegram bot.

In this tutorial, you will learn step-by-step how to build a fully functional, production-ready Telegram notification bot using Python, Django REST Framework, and PostgreSQL.

---

### Prerequisites & Architecture Overview

Before we start writing code, ensure you have:
1. Python 3.10+ and Django installed in your virtual environment.
2. A PostgreSQL database connected to your Django application.
3. A public HTTPS URL (or Ngrok during local development) for receiving webhook requests from Telegram.

Our architecture consists of four main building blocks:
1. **Bot Creation:** Obtaining an API Access Token from Telegram's BotFather.
2. **Database Model:** Storing subscriber chat IDs and preference states in PostgreSQL.
3. **Webhook Handler View:** A Django REST endpoint receiving incoming Telegram webhook JSON updates.
4. **Broadcasting Engine:** A Python utility that iterates over active subscribers and broadcasts real-time alert messages via HTTP POST requests to Telegram's Bot API.

---

### Step 1: Registering Your Bot with BotFather

Open your Telegram desktop or mobile app and search for `@BotFather`. Start a conversation and send the `/newbot` command:

```bash
# Telegram Chat Session with @BotFather
/newbot
# Response: Alright, a new bot. How are we going to call it? Please choose a name.
RecruitmentAlert Bot

# Response: Good. Now let's choose a username. It must end in `bot`.
govalerts_bot

# Response: Done! Congratulations on your new bot.
# Use this token to access the HTTP API:
# YOUR_TELEGRAM_BOT_TOKEN_HERE
```

Save your token securely in your Django `.env` file:

```bash
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
```

---

### Step 2: Defining the Subscriber Model in PostgreSQL

In your Django app (e.g. `apps/bot/models.py`), create a database model to track users who interact with your bot.

```python
# apps/bot/models.py
from django.db import models
from django.utils import timezone

class TelegramSubscriber(models.Model):
    chat_id = models.BigIntegerField(unique=True, db_index=True, help_text="Telegram User/Chat ID")
    username = models.CharField(max_length=150, blank=True, default='')
    first_name = models.CharField(max_length=150, blank=True, default='')
    is_active = models.BooleanField(default=True, db_index=True, help_text="Set false if user blocks the bot")
    subscribed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'telegram_subscribers'
        ordering = ['-subscribed_at']

    def __str__(self):
        return f"{self.first_name} ({self.chat_id})"
```

Run Django migrations to create the database table in PostgreSQL:

```bash
python manage.py makemigrations bot
python manage.py migrate bot
```

---

### Step 3: Writing the Webhook Handler View in Django

Telegram sends incoming messages as HTTP POST requests containing JSON updates. We will write a Django REST API view (`APIView`) decorated with `@csrf_exempt` to handle incoming `/start` and `/help` commands.

```python
# apps/bot/views.py
import os
import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import TelegramSubscriber

logger = logging.getLogger(__name__)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(APIView):
    def post(self, request):
        data = request.data
        if not data or "message" not in data:
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)

        message = data["message"]
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()
        first_name = message.get("from", {}).get("first_name", "")
        username = message.get("from", {}).get("username", "")

        if not chat_id:
            return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)

        # Handle /start Command
        if text.startswith("/start"):
            subscriber, created = TelegramSubscriber.objects.get_or_create(
                chat_id=chat_id,
                defaults={
                    "first_name": first_name,
                    "username": username,
                    "is_active": True,
                }
            )
            if not subscriber.is_active:
                subscriber.is_active = True
                subscriber.save()

            welcome_msg = (
                f"Hello {first_name}! Welcome to RecruitmentAlert.\\n\\n"
                "You are now subscribed to receive instant alerts whenever "
                "official Nigerian federal government recruitment portals open."
            )
            self.send_telegram_message(chat_id, welcome_msg)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    def send_telegram_message(self, chat_id: int, text: str):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
```

Register the view URL in your Django `urls.py`:

```python
# apps/bot/urls.py
from django.urls import path
from .views import TelegramWebhookView

urlpatterns = [
    path('webhook/', TelegramWebhookView.as_view(), name='telegram_webhook'),
]
```

---

### Step 4: Registering the Webhook URL with Telegram API

To instruct Telegram to forward incoming updates to your Django endpoint, send a HTTP GET or POST request to Telegram's `setWebhook` endpoint:

```bash
# Register Webhook with Telegram
curl -X POST "https://api.telegram.org/bot7192847192:AAH9f2kLskP19823k_ExampleTokenHere/setWebhook" \\
     -H "Content-Type: application/json" \\
     -d '{"url": "https://www.recruitmentalert.com.ng/telegram/webhook/"}'
```

Response verification:
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

---

### Step 5: Broadcasting Real-Time Notifications

When a new verified recruitment opening is created in Django, call this broadcasting service function to deliver alerts to all active subscribers.

```python
# apps/bot/services.py
import os
import requests
import logging
from .models import TelegramSubscriber

logger = logging.getLogger(__name__)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def broadcast_recruitment_alert(job_title: str, agency_name: str, portal_url: str):
    subscribers = TelegramSubscriber.objects.filter(is_active=True)
    success_count = 0
    failure_count = 0

    message_text = (
        f"🚨 **VERIFIED RECRUITMENT ALERT**\\n\\n"
        f"**Agency:** {agency_name}\\n"
        f"**Position:** {job_title}\\n\\n"
        f"**Official Portal:** [Apply Here]({portal_url})\\n\\n"
        f"⚡ *Government recruitment is 100% free. Never pay for job forms.*"
    )

    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for sub in subscribers:
        payload = {
            "chat_id": sub.chat_id,
            "text": message_text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        try:
            res = requests.post(api_url, json=payload, timeout=5)
            if res.status_code == 200:
                success_count += 1
            elif res.status_code == 403:
                sub.is_active = False
                sub.save()
                failure_count += 1
            else:
                failure_count += 1
        except Exception as err:
            logger.error(f"Error broadcasting to {sub.chat_id}: {err}")
            failure_count += 1

    return {"success": success_count, "failed": failure_count}
```

---

### Conclusion

You now have a production-ready, asynchronous notification system integrated with Python, Django, PostgreSQL, and Telegram. This architecture ensures high deliverability, automated subscriber state management, and real-time alerts for thousands of users.
"""

NNPC_BODY = """Searching for a job in Nigeria can be challenging, but dealing with fraudsters impersonating major federal agencies makes it exhausting. The Nigerian National Petroleum Company Limited (NNPC) is one of the most targeted institutions by recruitment scammers. Every year, thousands of unsuspecting job seekers fall victim to fake NNPC recruitment portals, losing millions of Naira in fraudulent application fees and scratch card processing payments.

At RecruitmentAlert, our automated monitoring system continuously audits official Nigerian government portals to protect job seekers. Below are the 7 definitive warning signs that an NNPC recruitment notification is fraudulent.

---

### 1. The Website URL Does Not End in .nnpcgroup.com
This is the single most important rule. Official NNPC recruitment notices are published strictly on their verified enterprise domain: **https://www.nnpcgroup.com** or dedicated subdomains like **careers.nnpcgroup.com**.

Scammers create fake websites using similar-sounding domain names like:
- `nnpcrecruitment2026-portal.online`
- `nnpc-job-portal.com.ng`
- `nnpc-careers-apply.site`

Always inspect the address bar in your browser. If the domain name does not end in `.nnpcgroup.com`, it is 100% fake. You can verify any official domain instantly on our Monitored Portals Directory.

---

### 2. You Are Asked to Pay an "Application Fee" or "Processing Charge"
**Legitimate Nigerian federal government recruitment processes are 100% free.** 

Fake websites will ask you to pay between ₦2,000 and ₦10,000 for:
- "Form processing fees"
- "Aptitude test registration"
- "Medical clearance screening pin"
- "Guarantor verification form"

No genuine Nigerian government agency (whether NNPC, Customs, EFCC, or Immigration) requires job applicants to transfer money into a bank account or pay via OPay/PalmPay.

---

### 3. Registration Forms Hosted on Free Platforms (Google Forms / Blogspot)
NNPC operates multi-billion Naira digital infrastructure. They will never collect application details, CVs, or National Identification Numbers (NIN) using Google Forms, Typeform, Blogspot, or WordPress sites.

If a link redirects you to a `forms.gle` or `blogspot.com` page asking for personal credentials, close it immediately.

---

### 4. Pressure Tactics and Short Deadlines ("Closing in 24 Hours!")
Recruitment scams rely on urgency to make you act before thinking. You will often see countdown timers or messages stating:
*"NNPC Recruitment 2026 is closing today at midnight! Only 500 slots remaining!"*

Official federal recruitment drives run for multiple weeks (typically 3 to 6 weeks) to allow candidates from all 36 states and the FCT to submit their credentials. Deadlines are published formally in national newspapers and gazettes.

---

### 5. Telegram Groups or WhatsApp Admins Promising "Direct Placement"
Scammers set up Telegram channels and WhatsApp groups claiming to be run by "NNPC HR Directors" or "Board Members". They promise guaranteed employment slots in exchange for cash deposits.

RecruitmentAlert operates only one verified Telegram notification bot: **@govalerts_bot**. Our bot only sends alerts linking directly to official government portals and never accepts payments or private messages.

---

### 6. Grammatical Errors and Unprofessional Formatting
Official announcements from federal agencies pass through corporate communications and legal vetting. Fraudulent websites are usually rushed and filled with spelling mistakes, awkward phrasing, and mismatched agency logos.

Look out for strange capitalization, bad English, or obsolete logos (such as using the old NNPC Corporation emblem instead of NNPC Limited).

---

### 7. Demanding Your ATM Card PIN or BVN Details
No job application form requires your Bank Verification Number (BVN), ATM Card Number, Expiry Date, or CVV. Fake recruitment websites use form fields to steal your banking credentials and drain your bank account.

---

### Summary Checklist for NNPC Job Seekers
Before applying or sharing any recruitment link on social media:
1. **Verify the URL:** Is it `nnpcgroup.com`?
2. **Check the Fee:** Is it free? (It must be).
3. **Audit the Endpoint:** Check our live Public Audit Log to confirm if our automated nodes detected an active change on the portal.
"""

GOV_LIST_BODY = """One of the most effective ways to protect yourself from recruitment scams in Nigeria is knowing the exact official portal address for every Federal Ministry, Department, and Agency (MDA).

Scammers build look-alike websites with URLs like `customs-recruitment.com` or `efcc-jobs.ng` to trap job seekers. To help Nigerian job seekers navigate authentic civil service recruitments, RecruitmentAlert maintains a continuously monitored directory of 42 federal agency portal endpoints.

Below is the verified master list for 2026 grouped by federal sector.

---

### Security, Armed Forces & Law Enforcement MDAs

1. **Nigerian Police Force (NPF)**
   - Official Portal: **https://www.policerecruitment.gov.ng**
   - Sector: Defense & Law Enforcement
   - Key Information: Annual constable and cadet officer recruitment. Recruitment is completely free.

2. **Economic and Financial Crimes Commission (EFCC)**
   - Official Portal: **https://www.efcc.gov.ng**
   - Sector: Anti-Corruption & Intelligence
   - Key Information: Detective Superintendent and Inspectorate Cadre intake notices are published on the main domain.

3. **Nigeria Customs Service (NCS)**
   - Official Portal: **https://customs.gov.ng**
   - Sector: Revenue & Border Security
   - Key Information: Support Superintendent and Inspectorate cadres. Always confirm on `customs.gov.ng`.

4. **Nigeria Immigration Service (NIS) / CDCFIB**
   - Official Portal: **https://cdcfib.career**
   - Sector: Civil Defence, Correctional, Fire & Immigration Services Board
   - Key Information: Joint recruitment portal for NIS, NSCDC, NCoS, and Federal Fire Service.

5. **National Drug Law Enforcement Agency (NDLEA)**
   - Official Portal: **https://www.ndlea.gov.ng**
   - Sector: Narcotics & Law Enforcement

---

### Federal Ministries & Civil Service Commission

6. **Federal Civil Service Commission (FCSC)**
   - Official Portal: **https://fcsc.gov.ng**
   - Sector: Federal Civil Service Administration
   - Key Information: Manages core recruitment into Federal Ministries (Education, Health, Works, Water Resources).

7. **Teachers' Registration Council of Nigeria (TRCN)**
   - Official Portal: **https://trcn.gov.ng**
   - Sector: Professional Education Vetting

8. **Universal Basic Education Commission (UBEC)**
   - Official Portal: **https://ubec.gov.ng**
   - Sector: Basic Education Development

---

### Financial, Revenue & Energy Institutions

9. **Nigerian National Petroleum Company Limited (NNPC)**
   - Official Portal: **https://www.nnpcgroup.com**
   - Sector: Energy & Oil

10. **Federal Inland Revenue Service (FIRS)**
    - Official Portal: **https://www.firs.gov.ng**
    - Sector: Federal Tax & Revenue

11. **Central Bank of Nigeria (CBN)**
    - Official Portal: **https://www.cbn.gov.ng**
    - Sector: Banking & Financial Regulation

12. **Nigerian Ports Authority (NPA)**
    - Official Portal: **https://nigerianports.gov.ng**
    - Sector: Maritime Infrastructure

---

### How RecruitmentAlert Verifies Portal Endpoints

Our automated monitoring engine audits all 42 MDA portals every 15 minutes. Here is what our system checks:

- **SSL & Domain Validation:** Confirms the portal uses valid EV SSL certificates registered to official Nigerian government authorities (`.gov.ng` or official corporate domains).
- **HTTP Reachability:** Verifies server response headers and latency from our Lagos monitoring node.
- **Content Change Detection:** Scans for actual job announcement updates, shortlists, and official press releases.
"""

NO_FEE_BODY = """One of the most persistent lies told to Nigerian job seekers is that you must pay for a "scratch card", "processing pin", or "guarantor registration fee" to apply for a federal government job.

This article explains the legal and regulatory framework that governs recruitment into Federal Ministries, Departments, and Agencies (MDAs) in Nigeria, and why **any website demanding payment for a government job form is 100% fraudulent.**

---

### 1. Federal Civil Service Rules Explicitly Prohibit Application Fees
Under the **Public Service Rules (PSR)** and guidelines established by the Federal Civil Service Commission (FCSC), recruitment into the public service is funded through budgetary appropriations approved by the National Assembly.

Government agencies are allocated funds specifically for:
- Publishing recruitment notices in national newspapers.
- Developing and maintaining digital recruitment portals.
- Conducting computer-based aptitude tests (CBT).
- Conducting physical screening and documentation.

Because these operational costs are covered by public funds, agencies are legally prohibited from charging job applicants.

---

### 2. Equal Opportunity and National Character Principles
Section 14(3) of the 1999 Constitution of the Federal Republic of Nigeria mandates the **Federal Character Principle**, which guarantees equal employment opportunities for citizens across all 36 states and the FCT.

Charging application fees creates an economic barrier that discriminates against low-income citizens and unemployed graduates. To uphold constitutional fairness, all official application processes are open and free to all qualified Nigerians.

---

### 3. Common Tactics Used by Scam Portals
Fraudsters exploit the desperation of job seekers by inventing realistic-sounding fee justifications:

- *"₦3,000 for Portal Maintenance & CBT Slot Reservation"*
- *"₦5,000 for Medical Examination & Clearance Pin"*
- *"₦10,000 for Uniform Measurement & Biometric Verification"*

These fees are collected through personal bank accounts, fintech wallet apps (OPay, PalmPay, Moniepoint), or fake payment gateways. Once the money is sent, the scammers disappear or block the victim.

---

### 4. How Official Agencies Communicate
Genuine agencies publish recruitment drives through official channels:
- Official government websites ending in `.gov.ng` or official corporate domains (e.g. `nnpcgroup.com`).
- Verified social media handles (Twitter/X, LinkedIn) with official verification checkmarks.
- National daily newspapers (Daily Trust, Punch, Vanguard, The Guardian).

They will never contact you via private WhatsApp messages, personal Gmail addresses, or unofficial Telegram groups demanding money for "guaranteed placement".
"""

class Command(BaseCommand):
    help = 'Seed the database with default recruitment guides and tech tutorials'

    def handle(self, *args, **options):
        self.stdout.write("Seeding blog posts...")

        posts_data = [
            {
                "title": "How to spot a fake NNPC recruitment",
                "slug": "how-to-spot-a-fake-nnpc-recruitment",
                "category": "recruitment",
                "author": "Shamsuddeen Yusuf",
                "meta_description": "Learn how to identify fake NNPC recruitment websites, fraudulent WhatsApp groups, and scam portal URLs before wasting your time and money.",
                "excerpt": "Learn how to identify fake NNPC recruitment websites, fraudulent WhatsApp groups, and scam portal URLs before wasting your time and money.",
                "published_date": timezone.now() - timezone.timedelta(days=5),
                "body": NNPC_BODY,
            },
            {
                "title": "Official gov.ng recruitment portals the complete verified list for 2026",
                "slug": "official-gov-ng-recruitment-portals-the-complete-verified-list-for-2026",
                "category": "recruitment",
                "author": "Shamsuddeen Yusuf",
                "meta_description": "The master verified directory of official Nigerian federal agency recruitment portals. Bookmark this page to avoid fake job sites.",
                "excerpt": "The master verified directory of official Nigerian federal agency recruitment portals. Bookmark this page to avoid fake job sites.",
                "published_date": timezone.now() - timezone.timedelta(days=3),
                "body": GOV_LIST_BODY,
            },
            {
                "title": "Why legitimate Nigerian government jobs never ask for payment",
                "slug": "why-legitimate-nigerian-government-jobs-never-ask-for-payment",
                "category": "recruitment",
                "author": "Shamsuddeen Yusuf",
                "meta_description": "Understand federal civil service regulations, anti-graft laws, and why any job portal demanding money is guaranteed to be a scam.",
                "excerpt": "Understand federal civil service regulations, anti-graft laws, and why any job portal demanding money is guaranteed to be a scam.",
                "published_date": timezone.now() - timezone.timedelta(days=2),
                "body": NO_FEE_BODY,
            },
            {
                "title": "How to build a Telegram bot with Python and Django that sends automatic notifications",
                "slug": "how-to-build-a-telegram-bot-with-python-and-django-that-sends-automatic-notifications",
                "category": "tech",
                "author": "Shamsuddeen Yusuf",
                "meta_description": "A complete step-by-step developer guide on building an automated notification Telegram bot using Python, Django REST Framework, and PostgreSQL.",
                "excerpt": "Learn how to build an automated Telegram notification bot in Python and Django. Step-by-step tutorial covering BotFather configuration, webhook handlers, storing chat IDs in PostgreSQL, and broadcasting messages.",
                "published_date": timezone.now(),
                "body": TECH_ARTICLE_BODY,
            }
        ]

        for p_data in posts_data:
            post, created = BlogPost.objects.update_or_create(
                slug=p_data["slug"],
                defaults=p_data
            )
            status_str = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{status_str} post: '{post.title}' ({post.category})"))

        self.stdout.write(self.style.SUCCESS("Successfully seeded all blog posts."))
