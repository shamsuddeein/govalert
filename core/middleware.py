"""
Global Visitor Tracking Middleware for GovAlert.
Intercepts public requests and updates Redis/Cache visitor telemetry.
"""
import hashlib
import logging
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


BOT_USER_AGENTS = (
    'bot', 'crawler', 'spider', 'slurp', 'googlebot', 'bingbot', 'yandex',
    'duckduckbot', 'facebookexternalhit', 'twitterbot', 'telegrambot',
    'whatsapp', 'python-requests', 'scrapy', 'curl', 'wget', 'gptbot',
    'claudebot', 'perplexitybot', 'bytespider', 'semrushbot', 'ahrefsbot',
    'mj12bot', 'headlesschrome', 'puppeteer', 'playwright'
)


def is_bot_user_agent(user_agent: str) -> bool:
    ua = (user_agent or '').lower()
    return any(b in ua for b in BOT_USER_AGENTS)


class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Do not record admin API endpoints, static assets, or health checks
        path = request.path
        if (
            path.startswith('/api/v1/admin/') or
            path.startswith('/admin/') or
            path.startswith('/static/') or
            path.startswith('/media/') or
            path == '/api/v1/health/' or
            path == '/favicon.ico'
        ):
            return response

        # Only record successful 200/304 HTTP responses
        if response.status_code in (200, 304):
            try:
                self._record_visitor(request)
            except Exception as exc:
                logger.debug(f"Visitor tracking exception: {exc}")

        return response

    def _record_visitor(self, request):
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '127.0.0.1')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_bot = is_bot_user_agent(user_agent)
        today_str = timezone.now().strftime('%Y-%m-%d')
        now_ts = int(timezone.now().timestamp())

        # 1. Track active online visitor (15 min sliding window = 900 seconds)
        cache.set(f"visitor_online_{ip}", now_ts, timeout=900)

        # 2. Track daily unique visitor IP hash
        ip_hash = hashlib.md5(f"{ip}_{today_str}".encode('utf-8')).hexdigest()
        if not cache.get(f"visitor_daily_{ip_hash}"):
            cache.set(f"visitor_daily_{ip_hash}", True, timeout=86400)
            try:
                cache.incr(f"visitors_count_{today_str}", delta=1)
            except Exception:
                cache.set(f"visitors_count_{today_str}", 1, timeout=86400 * 7)

        # 3. Track Bot vs Human hits
        if is_bot:
            try:
                cache.incr(f"bot_hits_{today_str}", delta=1)
            except Exception:
                cache.set(f"bot_hits_{today_str}", 1, timeout=86400 * 7)
        else:
            try:
                cache.incr(f"human_hits_{today_str}", delta=1)
            except Exception:
                cache.set(f"human_hits_{today_str}", 1, timeout=86400 * 7)

        # 4. Increment total page views today
        try:
            cache.incr(f"page_views_{today_str}", delta=1)
        except Exception:
            cache.set(f"page_views_{today_str}", 1, timeout=86400 * 7)

        # 5. Increment all time cumulative page views
        try:
            cache.incr("all_time_visitors_count", delta=1)
        except Exception:
            cache.set("all_time_visitors_count", 1, timeout=None)


class APMMiddleware:
    """
    Application Performance Monitoring (APM) & Structured Logging Middleware.
    Tracks wall-clock execution time (ms) and SQL query counts for every request.
    Emits structured logs and flags views exceeding 500ms threshold.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import time
        import json
        from django.db import connection

        start_time = time.perf_counter()
        initial_queries = len(connection.queries) if settings.DEBUG else 0

        response = self.get_response(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        final_queries = len(connection.queries) if settings.DEBUG else 0
        db_queries = final_queries - initial_queries

        log_data = {
            'timestamp': timezone.now().isoformat(),
            'component': 'web',
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration_ms, 2),
            'db_queries': db_queries,
        }

        # Exclude static/media from APM logging noise
        if not (request.path.startswith('/static/') or request.path.startswith('/media/')):
            if duration_ms > 500.0:
                logger.warning(
                    f"SLOW VIEW DETECTED: {request.method} {request.path} "
                    f"took {duration_ms:.2f}ms (>500ms threshold) — DB Queries: {db_queries}",
                    extra={'structured_log': json.dumps(log_data)}
                )
            else:
                logger.info(
                    f"APM {request.method} {request.path} {response.status_code} "
                    f"in {duration_ms:.2f}ms (DB Queries: {db_queries})",
                    extra={'structured_log': json.dumps(log_data)}
                )

        return response

