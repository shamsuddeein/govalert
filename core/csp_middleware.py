"""
core/csp_middleware.py — Content Security Policy middleware.

Without a CSP, any XSS vulnerability (stored, reflected, or DOM-based) is
immediately exploitable: an attacker can load arbitrary scripts, exfiltrate
tokens and session cookies, inject fake content, or redirect to phishing pages.

This middleware adds CSP headers to every response.  The policy is intentionally
restrictive:
  - default-src 'none'       — deny everything not explicitly permitted
  - script-src 'self'        — only our own JS (no inline scripts, no CDNs)
  - style-src 'self'         — only our own CSS
  - img-src 'self' data:     — our images + data: URIs (needed for inline SVGs)
  - connect-src 'self'       — XHR/fetch to our own origin only
  - font-src 'self'          — our own fonts only
  - frame-ancestors 'none'   — no iframing (belt+suspenders alongside X-Frame-Options)
  - base-uri 'self'          — prevent base tag injection
  - form-action 'self'       — POST forms can only submit to our own origin

The Django admin uses inline styles and scripts, so the admin path gets a
slightly relaxed policy ('unsafe-inline' for scripts and styles only on admin
paths).  This is a conscious trade-off — the admin is behind a secret URL and
staff auth; the public API and Telegram webhook do not have this relaxation.

Override the policy per-response by setting response['Content-Security-Policy']
before this middleware runs (or by setting CONTENT_SECURITY_POLICY in settings).
"""
from django.conf import settings


# Public API and webhook — strictest possible policy.
_PUBLIC_CSP = (
    "default-src 'none'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "font-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)

# Django admin — needs 'unsafe-inline' because the admin renders inline styles
# and scripts (Django does not support nonce-based CSP for the built-in admin).
# This relaxation applies ONLY to the admin URL prefix.
_ADMIN_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "font-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)


class ContentSecurityPolicyMiddleware:
    """
    Adds Content-Security-Policy header to every response.
    Must be placed AFTER SecurityMiddleware in the MIDDLEWARE list.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        admin_url = getattr(settings, 'ADMIN_URL', 'admin').strip('/')
        self._admin_prefix = f'/{admin_url}/' if admin_url else '/_admin_disabled_/'

    def __call__(self, request):
        response = self.get_response(request)

        # Do not overwrite if the view already set a CSP (e.g. for a specific endpoint).
        if 'Content-Security-Policy' in response:
            return response

        if request.path.startswith(self._admin_prefix):
            response['Content-Security-Policy'] = _ADMIN_CSP
        else:
            response['Content-Security-Policy'] = _PUBLIC_CSP

        return response
