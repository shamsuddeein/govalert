# RecruitmentAlert (GovAlert)

RecruitmentAlert helps Nigerians find verified public-sector opportunities and avoid recruitment scams. It monitors official agency portals, detects meaningful changes, applies AI-assisted risk analysis, requires human approval, and delivers verified alerts through its API and Telegram bot.

## Core flow

1. Celery checks vetted government portals and records snapshots.
2. Changed content is parsed, classified, and scored for trust.
3. Every detected item enters a human review queue.
4. Approved alerts are published to the API and delivered to eligible Telegram subscribers.
5. Recruitment updates retain an event chain so job watchers receive subsequent changes.

## Stack

- Django + Django REST Framework
- PostgreSQL + Redis + Celery
- Telegram Bot API
- OpenAI for structured recruitment summaries and verification assistance, with a rule-based fallback
- Playwright, Requests, BeautifulSoup, and PDF parsing for portal monitoring

## Run locally

Copy `.env.example` to `.env`, set valid credentials, then use Docker:

```bash
docker compose up --build
```

The Django container applies migrations and loads the vetted portal data before serving the API. The service is available on port 80 through Nginx.

For a non-container development environment, create a virtual environment, install `requirements/development.txt`, configure `DATABASE_URL` and `REDIS_URL`, then run migrations before starting Django and Celery.

## Testing

```bash
DEBUG=True DJANGO_SETTINGS_MODULE=config.settings.development .venv/bin/pytest -q
```

## OpenAI Build Week notes

This repository was developed with OpenAI Codex assistance for code review, debugging, test coverage, deployment hardening, and documentation. The project uses OpenAI models for structured recruitment analysis; the Devpost demo should show the working product and explain the Codex and GPT-5.6 workflow used during development.

## Security and privacy

- Telegram webhook requests require Telegram's secret-token header.
- Automated findings remain pending until human approval.
- Telegram delivery requires an active account, opt-in consent, enabled alerts, and an active agency subscription.
