# GovAlert (RecruitmentAlert Nigeria)

GovAlert helps Nigerians find verified public-sector opportunities and avoid recruitment scams. It monitors official government portals, detects meaningful changes, applies AI-assisted risk analysis, requires human approval, and delivers verified alerts through its web platform, REST API, and Telegram bot.

---

## Modern Serverless Architecture (₦0/month on Vercel + Turso)

GovAlert is built as a unified, high-performance fullstack TypeScript platform:
- **Frontend & App Engine:** React 19, Vite 8, TanStack Router/Start, Tailwind CSS v4, Radix UI, Lucide Icons.
- **Database:** **[Turso](https://turso.tech/) (libSQL)** via `@libsql/client` + **Drizzle ORM** (runs serverless with sub-15ms edge latency, generous 9GB free tier).
- **Hosting & Compute:** **Vercel** serverless functions and edge runtime.
- **Background Portal Monitoring:** **Vercel Cron** (`vercel.json`) triggering a lightweight Cheerio crawler (`server/crawler.ts`).
- **AI Verification Engine:** OpenAI GPT-4o-mini structured anti-fraud extraction with a deterministic rule-based fallback (`server/detector.ts`).
- **Telegram Bot:** Serverless webhook handler (`server/telegram.ts`) powered by **grammY**.

*(Note: Legacy Django codebase is preserved in `legacy_django/` for reference).*

---

## Key Features

1. **Evidence-First Verification:** Every opportunity displays authentic `.gov.ng` source links, confidence scores (0–100%), anti-scam factors, and detection timelines.
2. **Public Link Verifier (`/verify`):** Citizens can paste any recruitment link or WhatsApp message to verify its authenticity before applying.
3. **Comprehensive Admin Review Queue (`/admin/alerts`):** Operators review AI-analyzed portal changes, inspect diffs, and 1-click approve or reject.
4. **Automated Telegram Delivery:** Approved opportunities are instantly broadcast to subscribed Telegram users and public channels.
5. **52 Pre-Vetted Federal & State MDAs:** FIRS, Nigeria Customs Service, Civil Service Commission, Police Force, NIS, etc.

---

## Quick Start (Local Development)

### Prerequisites
- Node.js 20+ (Node 24 tested)
- npm 10+

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment (Optional for local testing)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(By default, local development uses `file:./users.db` directly without requiring any external cloud setup!)*

### 3. Run Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view GovAlert.

### 4. Test Serverless API Endpoints
```bash
npx tsx scripts/test-api.ts
```

---

## Deploying to Vercel with Turso

### 1. Create your Turso Database
1. Sign up at [https://turso.tech](https://turso.tech) (Free tier).
2. Install the Turso CLI:
   ```bash
   # Windows (PowerShell)
   irm https://get.tur.so/install.ps1 | iex
   ```
3. Create a database:
   ```bash
   turso db create govalert
   turso db show govalert --url
   turso db tokens create govalert
   ```

### 2. Seed Turso with Existing Vetted Portals
Export all 52 pre-vetted agencies, 83 portals, 14 alerts, and 6 blog posts directly into your Turso database:
```bash
$env:TURSO_DATABASE_URL="libsql://govalert-yourusername.turso.io"
$env:TURSO_AUTH_TOKEN="your-turso-auth-token"
npm run db:migrate
```

### 3. Deploy to Vercel
1. Push your repository to GitHub.
2. Import the repository into [Vercel](https://vercel.com).
3. Add the following Environment Variables in the Vercel Dashboard:
   - `TURSO_DATABASE_URL`: Your Turso libSQL URL (`libsql://...`)
   - `TURSO_AUTH_TOKEN`: Your Turso auth token
   - `OPENAI_API_KEY`: (Optional) Your OpenAI API key for GPT-4o-mini extraction
   - `TELEGRAM_BOT_TOKEN`: (Optional) Telegram bot token from @BotFather
   - `TELEGRAM_CHANNEL_ID`: (Optional) Target channel for broadcast alerts
4. Click **Deploy**!

Vercel will automatically build the project and register the `/api/cron/monitor` background crawler.

---

## Scripts Reference

| Command | Description |
| :--- | :--- |
| `npm run dev` | Starts the Vite development server with SSR at `localhost:3000` |
| `npm run build` | Builds the production bundle for Vercel/Nitro |
| `npm run preview` | Previews the production build locally |
| `npm run db:migrate` | Migrates/seeds database from SQLite to Turso libSQL |
| `npm run db:studio` | Launches Drizzle Studio GUI for inspecting database rows |
| `npm run db:push` | Pushes schema changes directly to Turso |
