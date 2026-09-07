# GovAlert — Master Design Prompt
**Single source of truth. Supersedes all previous briefs.**
**Last updated: July 2026**

---

## 1. PRODUCT DEFINITION

This is the foundation. Every design decision follows from it.

> **GovAlert is a recruitment verification platform that happens to list government jobs.**

It is not a job board. It does not compete with Jobberman or LinkedIn.
It competes with misinformation. Its product is trust.

The primary question every component must answer:
**"Why should I trust this listing?"**

If a component cannot answer that question, it does not belong on the page.

---

## 2. FOUR DESIGN PILLARS

Before any component is built, it passes all four:

**Institutional** — Feels official without pretending to be a government website. Serious, precise, civic. References: GOV.UK, Cloudflare Status.

**Operational** — Everything communicates that monitoring is actively happening right now. Timestamps, scan intervals, uptime stats. Users should feel the system is alive.

**Explainable** — Nothing is a mysterious badge. Every value has evidence behind it. "VERIFIED" alone is not enough. Show what verified means.

**Evidence-first** — Never ask the user to simply trust you. Show the source, the timestamp, the portal URL, the check that was run. Trust is earned through proof, not design.

---

## 3. UI REFERENCES

Design language should sit at the intersection of:
- **GOV.UK** — clarity, no decoration, information first
- **GitHub** — information density, monospace data, status systems
- **Stripe Dashboard** — layout quality, spacing discipline, card design
- **Cloudflare Dashboard** — status monitoring, operational feel, data display

Not: startup landing pages, Nigerian bank apps, generic SaaS templates, news websites.

---

## 4. BRAND IDENTITY

### 4.1 Logo

**Icon:** A document outline with a single checkmark inside.
- Not a shield (that means antivirus/VPN — not GovAlert's category)
- Not a location pin (that means maps/delivery)
- Not a radar (too complex at 16px)
- A document with a checkmark directly communicates: "we check documents"
- Alternative: a signal beacon — two or three concentric arcs emanating from a point
- Must work at 16px favicon size and 200px header size
- Stroke-only, no fill, 1.5px stroke weight at base size

**Wordmark:** "Gov" in weight 700 + "Alert" in weight 400, IBM Plex Sans, same size
- The weight contrast within the name creates identity without a separate graphic treatment
- No all-caps, no letter spacing modifications

**Colors:**
- Light mode: icon in `#0a5c38`, wordmark in `#141414`
- Dark mode: icon in `#3fb68e`, wordmark in `#e8edf2`

### 4.2 Brand Mark

A `3px` solid horizontal line in `#006b3c` (Nigerian flag green) runs across the very top of every page, above the navbar. This is the brand mark. It appears on every page, every view, including mobile. It is the one persistent identity element.

### 4.3 Tagline

"Verified recruitment intelligence."

That is all. No "Straight from the source." No "Data you can trust." One sentence, full stop.

---

## 5. COLOR SYSTEM

All values are custom. No Tailwind default palette colors used unmodified.

```css
/* Brand */
--green-primary:    #0a5c38;   /* main CTA, verified states, active indicators */
--green-hover:      #08472d;   /* button hover */
--green-accent:     #3fb68e;   /* primary green on dark backgrounds */
--green-tint:       #f0faf6;   /* subtle hover backgrounds in light mode */
--green-nigeria:    #006b3c;   /* top brand line only */

/* Backgrounds */
--bg-page-light:    #f5f3ef;   /* warm off-white — never pure white */
--bg-page-dark:     #0c1015;   /* deep near-black */
--bg-card-light:    #ffffff;
--bg-card-dark:     #141a20;
--bg-elevated-dark: #1a2230;

/* Text */
--text-primary-light:   #141414;
--text-secondary-light: #5a6370;
--text-primary-dark:    #e8edf2;
--text-secondary-dark:  #8b9aad;

/* Borders */
--border-light:     #e2ddd6;
--border-dark:      #242c38;

/* Status — semantic, same in light and dark */
--status-verified:     #0a5c38;   /* deep green */
--status-urgent:       #b45309;   /* dark amber */
--status-new:          #0e6b8a;   /* teal */
--status-updating:     #3b4bbf;   /* indigo */
--status-closed-bg:    #e5e7eb;
--status-closed-text:  #6b7280;
--status-nochange-bg:  #f3f4f6;
--status-nochange-text:#9ca3af;

/* Alerts */
--gold:             #c8960c;   /* warnings, high priority indicators */
--error:            #b91c1c;   /* errors only */

/* Portal status */
--portal-online:    #0a5c38;
--portal-maintenance: #b45309;
--portal-offline:   #b91c1c;
```

**Rules:**
- Page background is `--bg-page-light` in light, `--bg-page-dark` in dark — never pure white or pure black
- Cards sit on top of the page background — this creates natural depth
- Green is the accent color, not the dominant color
- Primary brand color for non-green elements is deep slate — use `#1a2332` for things that need authority without green
- Status badge colors are the same in light and dark mode — they are semantic, not themed

---

## 6. TYPOGRAPHY

### Fonts
```
UI Font:      IBM Plex Sans   — all text, all sizes, all components
Mono Font:    IBM Plex Mono   — IDs, timestamps, scan logs, response data, codes only
```

**Never use:** Instrument Serif (removed), Inter, Poppins, Nunito, Roboto, or any font that is a default in any template builder. If it is a common AI-tool default, do not use it.

### Type Scale
```
10px  — micro labels (STAGE 1, column headers in tables)
11px  — overlines, technical badges, mono timestamps
12px  — captions, meta information, secondary labels
13px  — card metadata values, secondary body
14px  — nav links, form labels, button text
15px  — primary body text
17px  — card titles, list item headings
22px  — section subheadings
28px  — page headings (inner pages)
36px  — hero headline (mobile)
44px  — hero headline (desktop)
```

### Weight System
```
400 — body, descriptions, secondary text
500 — metadata values, emphasis within body
600 — card titles, nav active, section labels
700 — page headings, logo "Gov"
```

### Letter Spacing
```
Overlines and micro-labels:  0.08em uppercase
Mono data:                   -0.01em
All other text:              0
```

### Mono font usage — specific list
Use IBM Plex Mono ONLY for:
- REF numbers (REF: 8829-GA)
- Timestamps (10:23, 14 Jul 2026 08:43)
- Response time indicators
- Scan interval (15m cycle)
- Portal fingerprint hashes
- Confidence calculation breakdowns
- Technical audit log entries

Do not use mono for headings, body text, nav, or buttons.

---

## 7. SPACING SYSTEM

8px base grid. Every value is a multiple of 8.

```
8px   — tight internal spacing (icon-to-text gaps)
16px  — component internal padding (small)
20px  — grid gap between cards
24px  — card internal padding
32px  — section component spacing
48px  — section vertical padding (mobile)
64px  — section vertical padding (tablet)
96px  — section vertical padding (desktop)
```

**Border radius:**
```
6px   — badges, chips, small pills
8px   — cards, inputs, buttons
12px  — modals, sheets, overlays
50%   — circular elements only
```

Never exceed 12px on any non-circular element.

---

## 8. COMPONENT SYSTEM

### 8.1 Status Badge

Unified system. Used identically across every page and component.

```
Structure: [icon 10px] [label text]
Padding:   4px 10px
Radius:    6px
Font:      IBM Plex Sans 11px 600 uppercase letter-spacing 0.06em
```

| State | Background | Text | Icon |
|---|---|---|---|
| VERIFIED | `#0a5c38` | white | checkmark-circle |
| URGENT | `#b45309` | white | alert-triangle |
| NEW OPENING | `#0e6b8a` | white | plus-circle |
| UPDATING | `#3b4bbf` | white | refresh-cw |
| CLOSED | `#e5e7eb` | `#6b7280` | x-circle |
| NO CHANGES | `#f3f4f6` | `#9ca3af` | minus |

Same colors in light and dark mode. Status badges are semantic, not themed.

### 8.2 Job Card

```
┌─────────────────────────────────────────┐
│ REF: 8829-GA [mono 11px #9ca3af]    [BADGE] │
│                                           │
│ Job Title [IBM Plex Sans 17px 600]        │
│ Agency Name [13px 500 --green-primary]    │
│                                           │
│ ─────────────────────────────────────     │
│                                           │
│ Deadline      Positions                   │
│ Oct 24, 2024  Multiple Positions          │
│                                           │
│ Published     Verification                │
│ 2h ago        OFFICIAL SOURCE ↗           │
│                                           │
│                       View details →      │
└─────────────────────────────────────────┘
```

**Styling:**
- Background: `#ffffff` light / `--bg-card-dark` dark
- Border: `1px solid --border-light` / `1px solid --border-dark`
- Border-radius: 8px
- Padding: 24px
- Box-shadow light: `0 1px 3px rgba(0,0,0,0.06)`
- Hover: `translateY(-2px)` + `box-shadow: 0 6px 16px rgba(0,0,0,0.10)`, 200ms ease
- No colored left border — the badge provides all status context
- Grid: 3 col desktop / 2 col tablet / 1 col mobile, 20px gap

**Label row styling:**
- Labels (Deadline, Positions, etc.): 11px uppercase `--text-secondary`, 0.06em spacing
- Values: IBM Plex Sans 13px 500 `--text-primary`
- "OFFICIAL SOURCE ↗": IBM Plex Sans 12px 600, `--green-primary`, external-link icon

### 8.3 Agency Portal Card

```
┌─────────────────────────────────────────┐
│ [NNPC chip]              ○ VETTED 100%  │
│                                           │
│ NNPC Limited                              │
│ ● Online                                  │
│                                           │
│ ─────────────────────────────────────     │
│                                           │
│ Jobs available    Last checked            │
│ 1 active opening  ↺ 2 mins ago [mono]    │
│                                           │
│ Response time     Verification            │
│ ●●●               ████████████░░ 100%    │
│                                           │
│ Official website ↗         View profile → │
└─────────────────────────────────────────┘
```

**Response time dots (replace raw ms numbers):**
- `< 400ms` → ●●● (3 green dots) — Fast
- `400–700ms` → ●●○ (2 green, 1 empty) — Acceptable
- `> 700ms` → ●○○ (1 amber, 2 empty) — Slow
- Offline → ○○○ (3 empty, red tint) — Unreachable

**Vetted indicator:** Small circle (20px) with `O` outline, percentage text beside it. Not a filled ring — too complex at small sizes.

**Portal status dot:**
- Online: `--portal-online` filled dot
- Maintenance: `--portal-maintenance` filled dot
- Offline: `--portal-offline` filled dot

### 8.4 Confidence Indicator

This is what separates GovAlert from every job board. Show it on job detail and agency profile.

```
Verification

Confidence: 98%
[████████████████░░ progress bar]

Based on:
✓ Official .gov.ng domain confirmed
✓ Content matches previous announcement format
✓ No duplicate detected in 30-day window
✓ Historical recruitment pattern consistent
! Manual review: Not required

Source: recruitment.fedcivilservice.gov.ng
Checked: 14 Jul 2026, 08:43 WAT
```

**Rule:** Only display fields your backend actually computes. If your system does not produce a confidence score, this component does not appear. If the score is genuinely 60%, show 60% — do not hide low scores. Honest uncertainty is more trustworthy than consistent false precision.

### 8.5 Verification Timeline (Audit Log)

Used on job detail page and verification report page.

```
09:13  Announcement detected on NNPC portal
09:14  Domain verified: nnpcgroup.com/careers (.gov.ng confirmed)
09:14  Content extracted and fingerprinted
09:15  Duplicate check passed (no match in 30-day window)
09:16  Historical comparison: matches 2023 Graduate Trainee format
09:17  Confidence score calculated: 98%
09:17  Published to GovAlert feed and Telegram channel
```

Styling:
- Left column: IBM Plex Mono 11px timestamp, `--text-secondary`
- Right column: IBM Plex Sans 13px 400, `--text-primary`
- Each row separated by 12px vertical spacing
- Left border: `2px solid --border-light` with dot at each entry
- Most recent entry: dot filled green

### 8.6 Portal Status Row (Monitoring Section)

```
● 8 Online   ◐ 3 Maintenance   ○ 3 Down
11 campaigns · 15m cycle · Last audit 2m ago
```

- Each status item: colored dot + IBM Plex Sans 12px 500, 20px gap
- Second line: IBM Plex Mono 11px, `--text-secondary`
- Background: own strip with `1px` top and bottom border — separated from hero and cards

---

## 9. NAVBAR

**Desktop:**
```
[3px green line — top of page]
[Logo icon + wordmark]  [Home Jobs Agencies Verification About]  [🌙] [Sign In] [Get Alerts →]
```

- Height: 60px
- Bottom border: `1px solid --border-light` light / `1px solid --border-dark` dark
- Nav links: IBM Plex Sans 14px 500, `--text-secondary`, hover → `--green-primary` + left-to-right underline animation 200ms
- "Sign In": text only, 14px, `--text-secondary`
- "Get Alerts →": filled button, `--green-primary` bg, white text, 14px 600, 8px radius, 36px height, 16px horizontal padding, Telegram icon 14px left

**Mobile:**
- Logo left, dark mode toggle + hamburger icon right
- Hamburger opens full-screen overlay menu
- Menu items: IBM Plex Sans 18px 400, stacked with 32px spacing
- Legal links (Privacy Policy, Terms of Service) sit inside a "Legal" group with a label — not floating at the bottom of empty space
- "Get Alerts" button: full-width, at bottom of menu before legal section
- Close (×) button top-right of overlay

---

## 10. PAGE SPECIFICATIONS

### 10.1 Homepage

**Hero section:**

```
[Overline: ● FEDERAL RECRUITMENT MONITOR · LIVE]
[IBM Plex Mono 11px, --green-primary, 0.1em spacing]
[Pulsing dot animation]

[Headline: IBM Plex Sans 44px 600 line-height 1.15]
Nigeria's verified
recruitment intelligence.
[No italic. No serif. Plain weight. "intelligence" can be --green-primary color.]

[Subtext: IBM Plex Sans 15px 400, --text-secondary, max 360px]
Every federal recruitment verified from official
MDA portals. No rumors. No scams. Just facts.

[Buttons: horizontal, 16px gap]
[Browse Jobs — filled --green-primary] [Get Alerts — outline --green-primary + Telegram icon]

[Search bar: full width below, 16px margin-top]
[🔍 SVG icon — NOT emoji] [Search NNPC, Customs, EFCC...] [Search button]

[Quick tags: 12px below search]
[NNPC] [Customs] [EFCC] [NAF] [CBN] [FIRS]
— pill chips, 8px radius, 12px 600, border --border-light, hover: border --green-primary + --green-tint bg

[Show live feed ▾ — mobile only, collapsible]
[Live feed panel visible on desktop by default]
```

**Live feed panel (desktop — always visible, mobile — collapsible):**
```
Background: #0c1015 (always dark — even in light mode)
Border: 1px solid #1e2a38, 8px radius

Header: "LIVE FEED" [IBM Plex Mono 11px #3fb68e] [● pulsing] [Updated 2m ago right-aligned]
Divider: 1px #1e2a38

Each item:
  [Agency name — IBM Plex Sans 13px 600 #e8edf2]
  [Status badge] [Timestamp — mono 11px #5a6a7a right-aligned]
  Border-bottom: 1px #1e2a38

Footer: "11 campaigns active · 15m cycle" [mono 10px #3a4a5a]
```

**Portal status bar:**
```
Between hero and job listings.
Background: own row, border top + bottom 1px --border-light
Padding: 12px 0
Content: ● 8 Online  ◐ 3 Maintenance  ○ 3 Down  |  11 campaigns · 15m cycle · Last audit 2m ago
```

**Latest verified jobs section:**
- Section heading: IBM Plex Sans 26px 600
- Grid/Table toggle (preserve existing feature)
- Job cards in grid layout
- "View all listings →" right-aligned link

**Portal health section:**
- Section heading: IBM Plex Sans 26px 600
- Subtext: "Real-time monitoring of reachability and active openings."
- Agency portal cards in horizontal scroll on mobile, 2-col grid on tablet, 4-col on desktop

**Verification pipeline section:**
- Label: "AUDIT PIPELINE" — IBM Plex Mono 11px uppercase green
- Heading: "How verification works"
- Vertical stepper on mobile, horizontal stepper on desktop
- Each step: numbered circle (36px, border 2px --green-primary) → connecting line → next circle
- Step label: 11px mono uppercase green
- Step title: IBM Plex Sans 15px 600
- Step description: IBM Plex Sans 13px 400 secondary
- Animate on scroll: circles fill left to right, 150ms stagger

**Stay updated section:**
- Left-aligned text (not centered)
- Heading: 22px 600
- Body: 15px secondary, 2 lines max
- Button: same "Get Alerts" button style

---

### 10.2 Jobs Page (`/jobs`)

```
[Overline: ● REAL-TIME VERIFICATION ACTIVE — mono 11px green]
[Heading: "Federal Recruitments Feed" — 32px 700 left-aligned]
[Subtext: 15px secondary, 1 line]

[Search bar: full width 48px height]

[Filter row: 4 dropdowns in a line on desktop, 2×2 on mobile]
  [Agency ▾] [Category ▾] [Location ▾] [Status ▾]
  Each label above the dropdown in 10px mono uppercase

[Result row: "Showing 13 verified listings" left, "Sort: Recently Detected ↓" right]

[Job card grid: 3 col desktop / 2 col tablet / 1 col mobile]

[Pagination: prev / 1 2 3 / next — centered, minimal]
```

---

### 10.3 Agencies Page (`/agencies`)

```
[Badge: ✓ VETTING 13 ACTIVE GOVERNMENT REGISTRIES — mono 11px green dot]
[Heading: "Federal MDAs & Portal Directories" — 32px 700]
[Subtext: 1 line]

[Search + filter: same system as jobs page]

[Agency card grid: 3 col desktop / 2 col tablet / 1 col mobile]
```

Agency card — see component 8.3 above.

**Empty state (no recruitments for an agency):**
```
[Minimal icon: 48px, stroke only]
No active recruitment detected
Last checked: [timestamp]
This portal is being monitored. We will alert you when a recruitment appears.
[Subscribe to alerts for this agency — outline button]
```

---

### 10.4 Job Detail Page (`/jobs/8829-GA`)

**This is the most important page. Design this before the homepage.**

This is where most users arrive from Telegram. Mobile, direct link, already partially convinced. Your job: give them the evidence that confirms their trust.

```
[Breadcrumb: Home → Jobs → REF: 8829-GA]
[IBM Plex Mono 11px secondary]

[Status badge — top of page]

[Heading: Job title — IBM Plex Sans 28px 700]
[Agency name — 16px 500 --green-primary link]

[Top metadata row — 2 col grid:]
  Deadline          Official source
  Oct 24, 2024      NNPC Portal ↗

  Category          Location
  Engineering       Rivers State

  Positions         Published
  Multiple          2h ago

[Divider]

[VERIFICATION SECTION — this is the product]

  Heading: "Verification" — 17px 600

  Confidence: 98%
  [████████████████░░ — progress bar 200px wide]

  Based on:
  ✓ Official domain confirmed (nnpcgroup.com/careers)
  ✓ Content matches previous NNPC announcement format
  ✓ No duplicate in 30-day detection window
  ✓ Historical pattern consistent with 2023 Graduate Trainee
  ! Manual review: Not required

  Source URL: [nnpcgroup.com/careers/2024-graduate-trainee]
  — mono 12px, clickable, shows full URL

  Last monitored: 14 Jul 2026, 08:43 WAT
  — mono 11px secondary

[Divider]

[AUDIT LOG SECTION]

  Heading: "Detection Timeline" — 17px 600

  09:13  Announcement detected on NNPC portal
  09:14  Domain verified — official source confirmed
  09:14  Content extracted and fingerprinted
  09:15  Duplicate check: passed
  09:16  Historical comparison: consistent format
  09:17  Confidence: 98% — published to feed

  [Each line: mono timestamp left + sans description right]

[Divider]

[RECRUITMENT DETAILS SECTION]

  Heading: "Recruitment Details" — 17px 600
  [Full description from official source — if available]
  [Requirements, qualifications, how to apply]
  [Link to official application page — filled button]

[Divider]

[PORTAL STATUS SECTION]

  Heading: "Portal Status" — 17px 600

  [Agency acronym chip]  [● Online]
  Last checked: ↺ 2m ago
  Response time: ●●●
  Portal uptime: 99.8%
  [View full agency profile →]

[Divider]

[RELATED RECRUITMENTS]

  Heading: "Other verified recruitments" — 17px 600
  [2-3 job cards, horizontal scroll on mobile]
```

**Uncertainty state (when confidence is low):**
```
Confidence: 62%

Based on:
✓ Official domain confirmed
✗ Content format does not match previous announcements
? Manual review: Recommended

This listing was detected but could not be fully verified.
Review the official source before applying.

[View official source ↗]
```

**Offline state (portal down during last check):**
```
! Portal Offline During Last Check

We detected this listing but could not re-verify because
the NNPC portal was offline during our last scan.

Last successful verification: 13 Jul 2026, 22:11 WAT
We will re-verify when the portal comes back online.
```

---

### 10.5 Agency Profile Page (`/agencies/NNPC`)

**Second most important page after job detail.**

```
[Breadcrumb: Home → Agencies → NNPC]

[Agency header:]
  [Acronym chip — large, 18px]  [● Online]
  [Agency full name — 28px 700]
  [Official description — 2 lines, 15px secondary]

[Status row — top metrics:]
  Portal: Online
  Monitoring: Every 5 minutes
  Uptime: 99.8%
  Avg response: ●●● Fast
  Total recruitments detected: 14
  Last update: Today, 08:43

[Official portal link: ↗ nnpcgroup.com/careers]
[IBM Plex Sans 14px --green-primary]

[Divider]

[ACTIVE RECRUITMENTS]

  Heading: "Active Recruitments" — 17px 600
  [Job cards in 1-col list for this agency]

[Divider]

[RECRUITMENT HISTORY]

  Heading: "Recruitment History" — 17px 600

  Timeline list:
  14 Jul 2026 — Graduate Trainee (Engineering) detected
  12 Jul 2026 — Portal checked, no changes
  10 Jul 2026 — Application window opened
  08 Jul 2026 — Vacancy announced

  [Each entry: mono date left, description right, dot on left border line]

[Divider]

[PORTAL HEALTH]

  Heading: "Portal Health" — 17px 600

  Response time (30 days): [small line chart or dot history]
  Uptime: 99.8%
  Last 10 checks: ●●●●●●●●●○ (9 green, 1 red = offline once)
  Last offline: 13 Jul 2026, 03:12 WAT (recovered in 18 minutes)

[Divider]

[VERIFICATION TRACK RECORD]

  Heading: "Verification Track Record" — 17px 600
  Average confidence score: 96%
  Total announcements verified: 14
  False positives detected: 0
  Scam domains blocked: 3
```

---

### 10.6 Verification Report Page (`/verification/8829-GA`)

**The page no other platform has.**

```
[Heading: "Verification Report" — 28px 700]
[REF: 8829-GA — mono 13px secondary]

[Report metadata:]
  Generated: 14 Jul 2026, 09:17 WAT
  Status: VERIFIED
  Report ID: VR-2026-0714-8829

[Full audit timeline — see component 8.5]

[Confidence breakdown — see component 8.4]

[DNS verification:]
  Domain: nnpcgroup.com
  Registrar: NiRA (verified .ng registry)
  SSL certificate: Valid, expires Dec 2026
  Hosting: Matches known NNPC infrastructure

[Content fingerprint:]
  Page hash at detection: [mono hash]
  Previous known hash: [mono hash]
  Difference: New content detected

[Conclusion:]
  This recruitment was detected, verified, and published
  without manual intervention. The automated pipeline
  confirmed all four verification stages.

[Download report — outline button]
[Share report — outline button]
```

---

### 10.7 Sign In Page (`/sign-in`)

Simple. No decoration. Trust comes from restraint.

```
[Center column, max 400px, vertically centered]

[Logo — 32px height]
[Heading: "Sign in to GovAlert" — 22px 600]
[Subtext: "Save jobs and receive personalised alerts." — 14px secondary]

[Form:]
  Email
  [Input — 48px height, 8px radius, 1px border, focus: 2px --green-primary ring]

  Password
  [Input — same, with show/hide toggle]

  [Sign in — full width, filled --green-primary, 48px height, 600 weight]

  [Forgot password? — 13px --green-primary link, right-aligned]

[Divider: or]

[Continue with Google — outline button, full width, Google icon]

[No account? Create one — 13px center-aligned]
```

No background images. No decorative elements. No gradient. One column. The simplicity signals: this is a serious platform.

---

### 10.8 Applicant Dashboard (`/dashboard`)

```
[Top row:]
  [Heading: "Dashboard" — 26px 700]
  [● Live monitoring active — 13px --green-primary, inline right of heading]

[Sidebar — 240px, sticky:]
  [Logo — 24px height]
  [Nav items: icon + IBM Plex Sans 14px 500]
    Saved Jobs    [count badge if any]
    Notifications [dot badge if new]
    My Profile
    Settings
  [Active state: 3px left border --green-primary + --green-tint bg]

[Main content: Saved Recruitments]
  [Section label: "SAVED RECRUITMENTS" — mono 11px uppercase]
  ["2 jobs saved" — 13px secondary]

  [Job cards — same system as main cards, not a simplified version]

  [Empty state:]
    [48px document-check icon, stroke, --text-secondary]
    "No saved jobs yet"
    "Browse verified jobs" — outline button --green-primary
```

---

### 10.9 About Page (`/about`)

```
[Hero:]
  [Overline: "ABOUT GOVALERT" — mono 11px]
  [Heading: "Vetting Nigeria's public sector opportunities" — 32px 600]
  [Subtext: 2 lines, 15px secondary]
  [Background: plain --bg-page-light — no gradient, no pattern]

[Mission + Vision — side by side cards:]
  Each card has a 3px left border
  Mission: left border --green-primary
  Vision:  left border --gold
  Small icon (24px stroke), label (mono 11px uppercase), body (15px 400 secondary)

[Independent Verification System — 3 columns:]
  No cards. No boxes. Just type and space.
  Number: "01" — IBM Plex Sans 40px 700 --green-tint (very faint, behind text)
  Title: 16px 600
  Body: 14px 400 secondary

[Anti-Scam section:]
  Single card, full width
  Left border 3px --green-primary
  Body: 15px 400
  Button: "Start vetting searches →" — outline --green-primary

[Team/transparency section — if relevant data exists]
```

---

### 10.10 FAQ / Verification Page (`/faq`)

Minimal. Let the content speak.

```
[Heading: "Frequently Asked Questions" — 28px 700, center]
[Subtext: 1 line, center, secondary]

[Accordion items:]
  Each: IBM Plex Sans 15px 600 question + chevron icon
  Open state: body text 15px 400 secondary, 16px top padding
  Separator: 1px --border-light between items
  No background color on open items — just the text, no card box

[Keep questions focused on trust:]
  What is GovAlert?
  How do you verify a portal is authentic?
  Is GovAlert affiliated with the Federal Government?
  Do I pay to apply for listed jobs?
  What does the confidence score mean?
  How do I get alerts on Telegram?
```

---

## 11. FOOTER

```
[3px top border: --green-primary]
[Background: #f0ede8 light / #0a0e13 dark — different from page background]

[Top section — 2 col on desktop, stacked on mobile:]
  LEFT:
    [Logo]
    ["Verified recruitment intelligence." — 14px secondary]
    ["Independent monitoring. Not affiliated with the Federal Government." — 12px secondary]

  RIGHT:
    ["Get instant alerts for new verified recruitments." — 14px]
    [Get Alerts on Telegram — filled --green-primary button]

[Link columns — 3 col on desktop, 2 col on tablet, 1 col on mobile:]
  RESOURCES          PLATFORM           LEGAL
  Verification       Official Telegram  Privacy Policy
  Methodology        API Docs           Terms of Service
  Monitored Agencies
  System Status

[Bottom bar — 1px border top, 16px padding:]
  LEFT: "© 2024 GovAlert. Independent monitoring. Not affiliated with the Federal Government."
        — IBM Plex Sans 11px --text-secondary
  RIGHT: [● SYSTEMS OPERATIONAL — 11px, --green-primary, mono]
```

---

## 12. RESPONSIVE RULES

### Mobile (< 768px)
- 3px brand line at top: visible always
- Navbar: logo left, dark mode toggle + hamburger right
- Hamburger: full overlay with stacked nav items + Get Alerts button + Legal group at bottom
- Hero headline: 36px, no split across lines
- Hero subtext: 15px, 3 lines max
- Live feed: hidden by default, "Show live feed ▾" toggle
- Quick tags: horizontal scroll, no wrapping
- Job cards: single column, full width, 24px padding
- Agency cards: single column, full width
- Verification timeline: vertical stepper (not horizontal)
- Footer: single column, stacked
- Dashboard: sidebar collapses to bottom tab bar or hamburger toggle

### Tablet (768px – 1024px)
- Job cards: 2 columns
- Agency cards: 2 columns
- Live feed: visible, narrower than desktop
- Verification timeline: horizontal but compact

### Desktop (1024px+)
- Job cards: 3 columns
- Agency portal cards: 4 columns
- Live feed: always visible, 360px wide
- Verification timeline: horizontal stepper
- Max content width: 1184px centered

---

## 13. MICRO-INTERACTIONS

Only what serves the user. No decoration.

```css
/* Card hover */
transition: transform 200ms ease, box-shadow 200ms ease;
hover: translateY(-2px), box-shadow 0 6px 16px rgba(0,0,0,0.10)

/* Button hover */
transition: background 150ms ease;
hover: darken 10%

/* Button active */
transform: scale(0.98)

/* Live status dot */
@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(10, 92, 56, 0.5) }
  70%  { box-shadow: 0 0 0 6px rgba(10, 92, 56, 0) }
  100% { box-shadow: 0 0 0 0 rgba(10, 92, 56, 0) }
}
animation: pulse 2s infinite

/* Search focus */
outline: 2px solid var(--green-primary)
outline-offset: 2px
transition: outline 150ms ease

/* Nav link hover underline */
::after pseudo-element: width 0% → 100%, 200ms ease, 1px height, --green-primary

/* New live feed item entry */
from: translateX(20px), opacity 0
to: translateX(0), opacity 1
duration: 250ms ease
```

**Do not animate:**
- Background colors on page load
- Floating particles or blobs
- Gradient shifts
- Text (except number counters)
- Anything on page load that delays content

---

## 14. COPY RULES

Every word earns its place.

```
DO:
  "2 jobs saved"               NOT "2 JOB(S) BOOKMARKED"
  "1 active opening"           NOT "Jobs available: 1"
  "↺ 2m ago"                  NOT "Last checked: 2 mins ago"
  "Get Alerts"                 NOT "Join Telegram"
  "View profile"               NOT "View profile →..."
  "Official source ↗"          NOT "Official source" without icon
  "No openings detected"       NOT "Jobs available: 0"
  "Portal is under review"     NOT just "UNDER REVIEW" alone
  "Analyst Openings"           NOT "12 openings" (avoid dummy data)
  "Pending"                    OK — honest uncertainty is fine

DO NOT:
  Use "Straight from the source" anywhere
  Use "Data you can trust" anywhere
  Center body text except in specific CTA sections
  Use ellipsis (…) in UI labels or buttons
  Use em dashes (—) in cards — use colons or line breaks
  Capitalize "Government" mid-sentence unnecessarily
  Use "real-time" if the system checks every 15 minutes — say "monitored every 15 minutes"
  Use emojis anywhere in the UI (SVG icons only)
  Use passive voice in status messages — "Portal checked" not "Portal has been checked"
```

---

## 15. WHAT TO NEVER DO

No exceptions.

1. No Instrument Serif or any serif font anywhere in the UI
2. No shield icon for the logo
3. No location pin icon for the logo
4. No raw millisecond response times in the citizen-facing UI
5. No dummy "12 openings" or placeholder data — show real data or hide the field
6. No colored left border on job cards — badge is sufficient
7. No gradient backgrounds (solid colors only, except a specific intentional hero use if justified)
8. No border-radius above 12px on any non-circular element
9. No box-shadow above `0 8px 20px rgba(0,0,0,0.10)`
10. No pure white `#ffffff` as page background — use `#f5f3ef`
11. No standard unmodified Tailwind palette colors — all colors must be custom tokens
12. No emojis in the UI — use SVG icons (the 🔍 emoji in the search bar must be replaced)
13. No centered body text except in deliberate CTA sections
14. No confidence scores or verification fields that your backend does not actually produce
15. No status language that makes claims you cannot technically fulfill
16. No Privacy Policy / Terms of Service floating at the bottom of mobile menus — put them in a labeled Legal group

---

## 16. PRIMARY USER JOURNEY (Design this first)

**The Telegram-to-Web flow is the most important journey on GovAlert.**

The user:
1. Subscribed to your Telegram channel
2. Received an alert: "NNPC Graduate Trainee — VERIFIED ✓ — Deadline Oct 24 — Apply at [link]"
3. Taps the link
4. Lands on the job detail page (`/jobs/8829-GA`) on mobile
5. Already partially convinced — they just need confirmation

This user does not need to browse. They do not need the homepage. They need one thing: **confirmation that what they read on Telegram is real.**

Design the job detail page to answer in the first screen:
- What is this recruitment (title, agency, deadline)
- Is it verified (confidence score + source URL visible without scrolling)
- How do I apply (button, not buried)

Everything else on the page is evidence that supports those three answers.

---

## 17. EMPTY AND UNCERTAINTY STATES

Design these before the "everything is working" states. They reveal character.

**Agency portal offline:**
```
! Portal Offline
We cannot verify this listing because [Agency] portal
is currently unreachable.
Last successful check: 13 Jul 2026, 22:11 WAT
We will re-verify when the portal comes back online.
Monitoring continues every 15 minutes.
```

**No active recruitments for an agency:**
```
No active recruitment detected
[Agency] has no open recruitment on their portal.
Last checked: ↺ 2m ago
We are monitoring this portal. You will be notified
when a recruitment appears.
[Get alerts for [Agency] →]
```

**Change detected but unconfirmed:**
```
⚠ Update Detected — Verification Pending
We detected a change on this portal but have not yet
completed verification. Check back in a few minutes.
Detected: 14 Jul 2026, 09:13 WAT
Expected verification: by 09:20 WAT
```

**Low confidence listing:**
```
⚠ Confidence: 62% — Review Recommended
This listing was detected but could not be fully verified.
One or more checks did not pass. Review the official
source before applying.
[View official source ↗]
```

---

*End of master prompt. This supersedes all previous design documents.*
*Use this file directly with v0, Lovable, Bolt, or as a build reference.*