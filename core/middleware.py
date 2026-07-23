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

