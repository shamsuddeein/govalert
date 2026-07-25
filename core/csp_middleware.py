"""
core/csp_middleware.py : Security & Content Security Policy middleware.

Adds comprehensive security headers to every response sent by the Django backend:
  - Content-Security-Policy (default-src 'self', allows Google Fonts, Railway API, inline styles/scripts)
  - X-Frame-Options (DENY)
  - Cross-Origin-Opener-Policy (same-origin)
  - Strict-Transport-Security (max-age=31536000; includeSubDomains; preload)
"""
from django.conf import settings

_CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https://*.railway.app https://recruitmentalert.com.ng https://www.recruitmentalert.com.ng; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)


class ContentSecurityPolicyMiddleware:
    """
    Enforces CSP, X-Frame-Options, Cross-Origin-Opener-Policy, and HSTS headers.
    Must be placed AFTER SecurityMiddleware in MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Set CSP header if not explicitly overridden by view
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = _CSP_POLICY

        # Enforce clickjacking protection & opener policies
        response["X-Frame-Options"] = "DENY"
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return response
