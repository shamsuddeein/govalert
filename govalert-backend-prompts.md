# GovAlert — Backend API Prompts (Model-Accurate)
**These replace Prompts 7–12 from govalert-prompts.md**
**Use your actual model names and field names exactly as written here.**

---

## Important observations before you start

Read this before running any prompt.

**1. Alert is the job listing, not RecruitmentEvent.**
`alerts.Alert` is the user-facing record. `alerts.RecruitmentEvent` is the raw
detected event. Build the jobs API from Alert, not RecruitmentEvent.

**2. Alert already has a confidence system.**
`Alert.trust_score` (0–100), `Alert.ai_classification` (REAL/FAKE/UNCERTAIN),
`Alert.ai_confidence` (0–100), and `Alert.ai_red_flags` (JSON list) are all
already computed. The confidence indicator in the frontend design is already
backed by real data. Use it.

**3. Portal has 7 health states. Map them to 3 for the frontend.**
`Portal.health_status` choices: ONLINE, OFFLINE, BLOCKED, CAPTCHA,
RATE_LIMITED, MAINTENANCE, UNKNOWN.
Map to frontend:
  - ONLINE → "online"
  - OFFLINE → "offline"
  - BLOCKED, CAPTCHA, RATE_LIMITED, MAINTENANCE, UNKNOWN → "maintenance"

**4. Alert.deadline is a CharField(100), not a DateField.**
It stores human text like "October 24, 2024" or "Pending" or "Not specified".
Do not try to parse it as a date. Pass it as a string to the frontend.

**5. Alert.status (PENDING/APPROVED/REJECTED/HELD) controls what is public.**
Only show `status='APPROVED'` alerts to the public API. PENDING and HELD are
still being verified. REJECTED means it was fake. Never expose those.

**6. The frontend badge system maps like this:**
  - VERIFIED badge → Alert.is_verified=True AND ai_classification='REAL'
  - URGENT badge → Alert.event_type='RECRUITMENT_OPEN' AND Portal.priority='HIGH'
  - NEW OPENING badge → RecruitmentEvent.status='NEW' (via the FK)
  - UPDATING badge → Alert.status='PENDING' (recently detected, not yet approved)
  - CLOSED badge → RecruitmentEvent.event_type='RECRUITMENT_CLOSED'

---

## PROMPT B1 — Agencies list and detail endpoints

```
Using Django REST Framework, build two endpoints for agencies.
Use the exact model names agencies.Agency and agencies.Portal.

Install DRF if not already installed:
pip install djangorestframework django-filter

---

SERIALIZER 1: AgencyListSerializer
Fields from Agency model:
  - id
  - name
  - acronym
  - slug
  - description
  - category (the raw value: SECURITY, FINANCE, HEALTH etc.)
  - logo_url
  - vetted_score
  - is_active
  - avg_confidence_score
  - false_positives
  - scam_domains_blocked

Add these computed fields (SerializerMethodField):
  - portal_status: look at Agency.portals.all() and return the worst
    status using this priority: if any portal is ONLINE return "online",
    if all portals are in [BLOCKED, CAPTCHA, RATE_LIMITED, MAINTENANCE,
    UNKNOWN] return "maintenance", if all portals are OFFLINE return
    "offline". Default "unknown" if no portals.
  - last_checked_at: return the max(last_checked_at) across all portals
    for this agency
  - response_time_ms: return the average response_time_ms across all
    active portals for this agency, rounded to integer
  - jobs_available: count Alert.objects.filter(
    agency=instance, status='APPROVED', is_verified=True) only count
    alerts where the deadline has not passed (or deadline is not a valid
    date — include those since we cannot know if they are expired)
  - total_recruitments_detected: count all Alert.objects where
    agency=instance regardless of status

SERIALIZER 2: AgencyDetailSerializer (extends AgencyListSerializer)
Add all the above, plus:
  - subscriber_count (direct field from Agency)
  - total_alerts_sent (direct field from Agency)
  - portals: list all portals for this agency using PortalSerializer

SERIALIZER 3: PortalSerializer
Fields from Portal model:
  - id
  - name
  - url
  - health_status (raw value)
  - frontend_status (computed: map ONLINE→"online",
    OFFLINE→"offline", everything else→"maintenance")
  - last_checked_at
  - last_successful_check_at
  - last_change_detected_at
  - uptime_percentage
  - response_time_ms
  - response_speed_dots (computed: 3 if response_time_ms < 400,
    2 if between 400-700, 1 if above 700, 0 if None)
  - consecutive_failures
  - poll_interval
  - priority
  - confidence

---

VIEWSET: AgencyViewSet (ModelViewSet, read-only)
  - queryset: Agency.objects.filter(is_active=True).prefetch_related('portals')
  - list serializer: AgencyListSerializer
  - detail serializer: AgencyDetailSerializer
  - lookup_field: slug
  - ordering: portals__health_status (online first)
  - add filter backend for: category, portal health_status

---

GET /api/v1/agencies/
GET /api/v1/agencies/{slug}/

Add these to the router in api/urls.py.
```

---

## PROMPT B2 — Jobs list and detail endpoints

```
Using Django REST Framework, build two endpoints for job listings.
Use models alerts.Alert and alerts.RecruitmentEvent.
Only ever expose alerts where Alert.status = 'APPROVED'.

---

SERIALIZER 1: JobListSerializer
Fields from Alert model:
  - id
  - title
  - deadline (CharField — pass as-is, do not parse)
  - positions
  - source_url
  - created_at (this is "published_at" for the frontend)
  - is_verified
  - trust_score
  - ai_classification

Add computed fields:
  - ref: return the related RecruitmentEvent.event_id
    (via alert.recruitment_event.event_id)
  - agency_name: alert.agency.name
  - agency_acronym: alert.agency.acronym
  - agency_slug: alert.agency.slug
  - agency_logo_url: alert.agency.logo_url
  - category: alert.agency.category
  - location_state: alert.portal.location_state
  - frontend_status: compute the badge status using this logic:
      if RecruitmentEvent.event_type == 'RECRUITMENT_CLOSED':
          return 'closed'
      elif alert.is_verified and alert.ai_classification == 'REAL':
          return 'verified'
      elif alert.portal.priority == 'HIGH' and
           alert.event_type == 'RECRUITMENT_OPEN':
          return 'urgent'
      elif alert.recruitment_event.status == 'NEW':
          return 'new_opening'
      elif alert.status == 'PENDING':
          return 'updating'
      else:
          return 'verified'

SERIALIZER 2: JobDetailSerializer (extends JobListSerializer)
Add all the above, plus:
  - requirements
  - content_excerpt
  - ai_confidence
  - ai_red_flags
  - sent_at
  - report_count

  Add confidence_factors (SerializerMethodField):
  Build a list of dicts. For each item: {"label": str, "passed": bool}.
  Rules:
    - {"label": "Official domain confirmed", "passed": True}
      if portal.url domain matches any of agency.official_domains
    - {"label": "AI classification: REAL", "passed": True}
      if alert.ai_classification == 'REAL'
    - {"label": "No duplicate detected", "passed": True}
      always True for approved alerts (dedup happened at ingestion)
    - {"label": "Historical pattern consistent", "passed": True}
      if alert.trust_score >= 70
    - {"label": "No red flags detected", "passed": True}
      if len(alert.ai_red_flags) == 0, else False
    - For each item in ai_red_flags, add:
      {"label": f"⚠ {flag}", "passed": False}

  Add detection_timeline (SerializerMethodField):
  Build a list of dicts: {"time": str, "event": str}
  Pull from:
    1. alert.recruitment_event.created_at → "Announcement detected on portal"
    2. alert.created_at → "Alert created and queued for verification"
    3. alert.verified_at (if not null) → "Verified and approved"
    4. alert.sent_at (if not null) → "Published to feed and Telegram channel"
  Format times as "HH:MM" using Africa/Lagos timezone.
  Sort by time ascending.

  Add portal_info (SerializerMethodField):
  Return a dict:
    - name: alert.portal.name
    - url: alert.portal.url
    - health_status: alert.portal.health_status
    - frontend_status: (same mapping as above: online/offline/maintenance)
    - last_checked_at: alert.portal.last_checked_at
    - response_speed_dots: 3/<400ms, 2/400-700ms, 1/>700ms
    - uptime_percentage: alert.portal.uptime_percentage

  Add related_jobs (SerializerMethodField):
  Return 3 other approved, verified alerts from the same agency,
  excluding the current alert. Use JobListSerializer for each.
  Return empty list if none exist.

---

VIEWSET: AlertViewSet (ReadOnlyModelViewSet)
  - queryset: Alert.objects.filter(status='APPROVED')
    .select_related('agency', 'portal', 'recruitment_event')
    .order_by('-created_at')
  - list serializer: JobListSerializer
  - detail serializer: JobDetailSerializer
  - lookup_field: 'recruitment_event__event_id'
  - lookup_url_kwarg: 'ref'
  - add filter backends for: agency__acronym, agency__category,
    portal__location_state, frontend_status, search (title + agency name)
  - ordering options: -created_at (default), deadline, -trust_score

GET /api/v1/jobs/
GET /api/v1/jobs/{ref}/   (ref = event_id like "8829-GA")

Add to router in api/urls.py.
```

---

## PROMPT B3 — System status and live feed endpoints

```
Build two endpoints for system-level monitoring data.
Use models monitor.PortalHealthLog, agencies.Portal,
monitor.Snapshot, and alerts.Alert.

---

ENDPOINT 1: GET /api/v1/status/

This is a function-based view (not a viewset).
Cache the response for 60 seconds using Django's cache framework.

from django.core.cache import cache
from django.utils import timezone
import datetime

Logic:
  today = timezone.now().date()
  
  1. agency_counts: query Portal.objects.filter(is_active=True)
     and group by health_status to get:
       - online: count where health_status='ONLINE'
       - offline: count where health_status='OFFLINE'
       - maintenance: count where health_status in
         ['BLOCKED','CAPTCHA','RATE_LIMITED','MAINTENANCE','UNKNOWN']
  
  2. today_health: aggregate from PortalHealthLog.objects.filter(date=today):
       - total_checks: Sum('checks_total')
       - successful_checks: Sum('checks_successful')
       - failed_checks: Sum('checks_failed')
       - changes_detected: Sum('changes_detected')
       - alerts_triggered: Sum('alerts_triggered')
     If no PortalHealthLog records exist for today yet, default all to 0.
  
  3. success_rate: calculate as:
     (successful_checks / total_checks * 100) if total_checks > 0 else 0
     Round to 2 decimal places.
  
  4. last_audit_at: Portal.objects.filter(is_active=True)
     .aggregate(Max('last_checked_at'))['last_checked_at__max']
  
  5. active_campaigns: Alert.objects.filter(status='APPROVED').count()
  
  6. system_operational: True if online count > offline count

  Return JSON:
  {
    "agencies_online": int,
    "agencies_offline": int,
    "agencies_maintenance": int,
    "total_agencies": int,
    "total_checks_today": int,
    "successful_checks_today": int,
    "failed_checks_today": int,
    "success_rate_today": float,
    "changes_detected_today": int,
    "alerts_triggered_today": int,
    "active_campaigns": int,
    "monitoring_interval_minutes": 15,
    "last_audit_at": ISO datetime string or null,
    "system_operational": bool
  }

Cache key: "system_status_v1"
Cache timeout: 60 seconds

---

ENDPOINT 2: GET /api/v1/status/live-feed/

Returns the 10 most recent monitoring events.
Cache for 30 seconds.

Logic:
  Pull the 10 most recent Snapshot records where has_change=True
  OR triggered_alert=True, ordered by -created_at.
  For each Snapshot:
    - agency_name: snapshot.portal.agency.name
    - agency_acronym: snapshot.portal.agency.acronym
    - event_type: determine badge:
        if snapshot.triggered_alert: check the Alert created closest
          to this snapshot time for the same portal, use its
          frontend_status logic. Default to "verified".
        elif snapshot.has_change: return "no_changes" ← actually
          use "new_opening" if has_change=True without triggered_alert
        else: return "no_changes"
    - event_time: snapshot.created_at as ISO string
    - time_ago: human readable relative time
      (use a helper: "Xm ago" under 60 min, "Xh ago" under 24h, "Xd ago" otherwise)

  Also include the 10 most recent Portal checks regardless of change:
  Query the 10 most recent Snapshot records (no filter on has_change).
  For each:
    - event_type: "no_changes" if has_change=False, else as above

  Merge and deduplicate, sort by event_time desc, return first 10.

  Return JSON:
  {
    "feed": [
      {
        "agency_name": str,
        "agency_acronym": str,
        "event_type": str,
        "event_time": ISO datetime str,
        "time_ago": str
      }
    ]
  }

---

Add both to api/urls.py:
  path('status/', status_view),
  path('status/live-feed/', live_feed_view),
```

---

## PROMPT B4 — URL routing and DRF settings

```
Set up the complete API routing for this Django project.

1. In settings.py, add to INSTALLED_APPS:
   'rest_framework',
   'django_filters',
   'corsheaders',

   Install if missing:
   pip install djangorestframework django-filter django-cors-headers

2. Add to MIDDLEWARE (must be before CommonMiddleware):
   'corsheaders.middleware.CorsMiddleware',

3. Add to settings.py:
   REST_FRAMEWORK = {
       'DEFAULT_PERMISSION_CLASSES': [
           'rest_framework.permissions.AllowAny',
       ],
       'DEFAULT_AUTHENTICATION_CLASSES': [],
       'DEFAULT_FILTER_BACKENDS': [
           'django_filters.rest_framework.DjangoFilterBackend',
           'rest_framework.filters.SearchFilter',
           'rest_framework.filters.OrderingFilter',
       ],
       'DEFAULT_PAGINATION_CLASS':
           'rest_framework.pagination.PageNumberPagination',
       'PAGE_SIZE': 20,
   }

   CORS_ALLOWED_ORIGINS = [
       'http://localhost:3000',
       'http://localhost:8081',
       'https://govalert-henna.vercel.app',
   ]

   CORS_ALLOW_ALL_ORIGINS = False

4. Create a new file: api/urls.py
   from rest_framework.routers import DefaultRouter
   from .views import AgencyViewSet, AlertViewSet

   router = DefaultRouter()
   router.register(r'agencies', AgencyViewSet, basename='agency')
   router.register(r'jobs', AlertViewSet, basename='job')

   urlpatterns = router.urls + [
       path('status/', status_view),
       path('status/live-feed/', live_feed_view),
   ]

5. In the main urls.py, add:
   path('api/v1/', include('api.urls')),

6. Test that these URLs resolve:
   /api/v1/agencies/
   /api/v1/agencies/nnpc/
   /api/v1/jobs/
   /api/v1/jobs/evt_20260711_000412/
   /api/v1/status/
   /api/v1/status/live-feed/
```

---

## PROMPT B5 — Seed all 41 agencies management command

```
Create a Django management command that seeds all 41 monitored
agencies into the database. Use get_or_create so it is safe to
run multiple times without creating duplicates.

File location: agencies/management/commands/seed_agencies.py

Use these exact agencies grouped by the Agency.category field choices.
Map to existing choices: SECURITY, FINANCE, UTILITIES, HEALTH,
EDUCATION, TRANSPORT, STATISTICS, JUDICIARY, OTHER.

Seed data:

SECURITY:
  {name: "Nigerian Army", acronym: "Army",
   official_domains: ["army.mil.ng"], category: "SECURITY"}
  {name: "Civil Defence, Correctional, Fire and Immigration Board",
   acronym: "CDCFIB", official_domains: ["cdcfib.gov.ng"], category: "SECURITY"}
  {name: "Department of State Services", acronym: "DSS",
   official_domains: ["dss.gov.ng"], category: "SECURITY"}
  {name: "Federal Fire Service", acronym: "FFS",
   official_domains: ["fedfire.gov.ng"], category: "SECURITY"}
  {name: "Nigerian Air Force", acronym: "NAF",
   official_domains: ["airforce.mil.ng"], category: "SECURITY"}
  {name: "Nigerian Correctional Service", acronym: "NCoS",
   official_domains: ["corrections.gov.ng"], category: "SECURITY"}
  {name: "Nigerian Defence Academy", acronym: "NDA",
   official_domains: ["nda.edu.ng"], category: "SECURITY"}
  {name: "Nigeria Immigration Service", acronym: "NIS",
   official_domains: ["immigration.gov.ng"], category: "SECURITY"}
  {name: "Nigeria Police Force", acronym: "NPF",
   official_domains: ["npf.gov.ng"], category: "SECURITY"}
  {name: "Nigeria Security and Civil Defence Corps", acronym: "NSCDC",
   official_domains: ["nscdc.gov.ng"], category: "SECURITY"}
  {name: "Nigerian Navy", acronym: "Navy",
   official_domains: ["navy.mil.ng"], category: "SECURITY"}

FINANCE:
  {name: "Economic and Financial Crimes Commission", acronym: "EFCC",
   official_domains: ["efcc.gov.ng"], category: "FINANCE"}
  {name: "Independent Corrupt Practices Commission", acronym: "ICPC",
   official_domains: ["icpc.gov.ng"], category: "FINANCE"}
  {name: "Central Bank of Nigeria", acronym: "CBN",
   official_domains: ["cbn.gov.ng"], category: "FINANCE"}
  {name: "Federal Inland Revenue Service", acronym: "FIRS",
   official_domains: ["firs.gov.ng"], category: "FINANCE"}
  {name: "Nigeria Customs Service", acronym: "NCS",
   official_domains: ["customs.gov.ng"], category: "FINANCE"}

UTILITIES (map Energy/Natural Resources to this):
  {name: "Nigerian National Petroleum Corporation", acronym: "NNPC",
   official_domains: ["nnpcgroup.com"], category: "UTILITIES"}
  {name: "Nigerian Upstream Petroleum Regulatory Commission",
   acronym: "NUPRC", official_domains: ["nuprc.gov.ng"],
   category: "UTILITIES"}
  {name: "Nigerian Midstream and Downstream Petroleum Regulatory Authority",
   acronym: "NMDPRA", official_domains: ["nmdpra.gov.ng"],
   category: "UTILITIES"}

HEALTH:
  {name: "Federal Ministry of Health", acronym: "FMOH",
   official_domains: ["health.gov.ng"], category: "HEALTH"}
  {name: "National Agency for Food and Drug Administration",
   acronym: "NAFDAC", official_domains: ["nafdac.gov.ng"],
   category: "HEALTH"}
  {name: "National Health Insurance Authority", acronym: "NHIA",
   official_domains: ["nhia.gov.ng"], category: "HEALTH"}

EDUCATION:
  {name: "Federal Ministry of Education", acronym: "FMOE",
   official_domains: ["education.gov.ng"], category: "EDUCATION"}
  {name: "National Universities Commission", acronym: "NUC",
   official_domains: ["nuc.edu.ng"], category: "EDUCATION"}
  {name: "National Board for Technical Education", acronym: "NBTE",
   official_domains: ["nbte.gov.ng"], category: "EDUCATION"}
  {name: "Joint Admissions and Matriculation Board", acronym: "JAMB",
   official_domains: ["jamb.gov.ng"], category: "EDUCATION"}

STATISTICS (map Identity/Civil Registration):
  {name: "National Identity Management Commission", acronym: "NIMC",
   official_domains: ["nimc.gov.ng"], category: "STATISTICS"}
  {name: "National Population Commission", acronym: "NPC",
   official_domains: ["population.gov.ng"], category: "STATISTICS"}

JUDICIARY:
  {name: "National Judicial Council", acronym: "NJC",
   official_domains: ["njc.gov.ng"], category: "JUDICIARY"}
  {name: "Supreme Court of Nigeria", acronym: "SCN",
   official_domains: ["supremecourt.gov.ng"], category: "JUDICIARY"}
  {name: "Federal Ministry of Justice", acronym: "FMJ",
   official_domains: ["justice.gov.ng"], category: "JUDICIARY"}

TRANSPORT:
  {name: "Federal Ministry of Works", acronym: "FMW",
   official_domains: ["works.gov.ng"], category: "TRANSPORT"}
  {name: "Nigerian Ports Authority", acronym: "NPA",
   official_domains: ["nigerianports.gov.ng"], category: "TRANSPORT"}
  {name: "Nigerian Maritime Administration and Safety Agency",
   acronym: "NIMASA", official_domains: ["nimasa.gov.ng"],
   category: "TRANSPORT"}
  {name: "Nigerian Civil Aviation Authority", acronym: "NCAA",
   official_domains: ["ncaa.gov.ng"], category: "TRANSPORT"}
  {name: "Nigerian Railway Corporation", acronym: "NRC",
   official_domains: ["nrc.gov.ng"], category: "TRANSPORT"}

OTHER (Communications + Agriculture):
  {name: "Nigerian Communications Commission", acronym: "NCC",
   official_domains: ["ncc.gov.ng"], category: "OTHER"}
  {name: "National Information Technology Development Agency",
   acronym: "NITDA", official_domains: ["nitda.gov.ng"],
   category: "OTHER"}
  {name: "Federal Ministry of Agriculture and Rural Development",
   acronym: "FMARD", official_domains: ["fmard.gov.ng"],
   category: "OTHER"}

For each agency:
  - auto-generate slug from acronym.lower()
  - set vetted_score = 85 (default)
  - set is_active = True
  - set description = "" (empty, fill manually later)
  - set logo_url = f"https://logo.clearbit.com/{official_domains[0]}?size=128"

After seeding, print a summary:
  "Created: X agencies"
  "Already existed: Y agencies"
  "Total in database: Z agencies"

Run with: python manage.py seed_agencies
```

---

## PROMPT B6 — Test all API endpoints

```
After building the API, test every endpoint to confirm it works.
Run these checks:

1. Start the Django development server:
   python manage.py runserver 8000

2. Test each URL and confirm the response shape:

   curl http://localhost:8000/api/v1/agencies/
   Expected: {"count": N, "results": [...], "next": null, "previous": null}
   Check: results array has agencies with portal_status field

   curl http://localhost:8000/api/v1/agencies/nnpc/
   Expected: single agency object with portals array

   curl http://localhost:8000/api/v1/jobs/
   Expected: {"count": N, "results": [...]}
   Check: results only contain status='APPROVED' alerts
   Check: each job has a "ref" field (event_id) and "frontend_status"

   curl http://localhost:8000/api/v1/jobs/{any_real_event_id}/
   Expected: single job with confidence_factors, detection_timeline,
             portal_info, related_jobs fields

   curl http://localhost:8000/api/v1/status/
   Expected: JSON with agencies_online, total_checks_today etc.
   Check: numbers are non-zero if the bot has been running

   curl http://localhost:8000/api/v1/status/live-feed/
   Expected: {"feed": [...]} with up to 10 items

3. Test filtering:
   curl "http://localhost:8000/api/v1/jobs/?agency__acronym=NNPC"
   curl "http://localhost:8000/api/v1/agencies/?category=SECURITY"
   curl "http://localhost:8000/api/v1/jobs/?search=police"

4. If any endpoint returns an error, paste the full traceback
   and fix it before moving to the frontend connection.

5. Confirm CORS works by making a fetch request from the browser
   console on the Vercel frontend domain to the API URL.
```

---

*These 6 prompts replace Prompts 7–12 from govalert-prompts.md.*
*Run them in order: B1 → B2 → B3 → B4 → B5 → B6*
*Do not start any frontend connection prompts until B6 passes.*
