"""
core/security.py — SSRF guard and outbound request safety.

Every URL the crawler visits comes from the Portal.url field in the database.
If an attacker gains write access to any Portal object (via admin compromise,
future injection, or insider threat) they can redirect the crawler to:

  - http://169.254.169.254/ (AWS metadata service — credential leak)
  - http://127.0.0.1:6379/  (Redis — unauthenticated command execution)
  - http://10.0.0.x/        (internal network scanning)
  - http://192.168.x.x/     (LAN scanning)
  - file:///etc/passwd       (local file read)

This module provides:
  1. validate_outbound_url() — must be called before every outbound HTTP request
     in the crawler. Resolves the domain to an IP and rejects private/reserved
     address space.
  2. A hard response size cap (10 MB) to prevent memory exhaustion from a
     malicious server sending an enormous response.
  3. TLS verification is ALWAYS enabled (verify=True). There is no legitimate
     reason to disable it globally — government portals with self-signed certs
     should have their CA added to the trust store, not have verification disabled.
"""
import ipaddress
import socket
import logging
from urllib.parse import urlparse

from core.exceptions import ScraperException

logger = logging.getLogger(__name__)

# Domains we always refuse to contact regardless of resolved IP.
_BLOCKED_DOMAINS = frozenset()

# Maximum response body size in bytes. A 500MB response from a "portal" is not
# a portal — it is a memory exhaustion attack.
MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MB

# Private and reserved IP ranges that must never be contacted.
_PRIVATE_NETWORKS = [
    ipaddress.ip_network('0.0.0.0/8'),        # "This" network
    ipaddress.ip_network('10.0.0.0/8'),        # RFC 1918 private
    ipaddress.ip_network('100.64.0.0/10'),     # Shared address space (RFC 6598)
    ipaddress.ip_network('127.0.0.0/8'),       # Loopback
    ipaddress.ip_network('169.254.0.0/16'),    # Link-local / AWS metadata service
    ipaddress.ip_network('172.16.0.0/12'),     # RFC 1918 private
    ipaddress.ip_network('192.0.0.0/24'),      # IETF protocol assignments
    ipaddress.ip_network('192.168.0.0/16'),    # RFC 1918 private
    ipaddress.ip_network('198.18.0.0/15'),     # Benchmark testing
    ipaddress.ip_network('198.51.100.0/24'),   # TEST-NET-2
    ipaddress.ip_network('203.0.113.0/24'),    # TEST-NET-3
    ipaddress.ip_network('224.0.0.0/4'),       # Multicast
    ipaddress.ip_network('240.0.0.0/4'),       # Reserved
    ipaddress.ip_network('255.255.255.255/32'),# Broadcast
    # IPv6
    ipaddress.ip_network('::1/128'),           # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),          # IPv6 unique local
    ipaddress.ip_network('fe80::/10'),         # IPv6 link-local
]


def _is_private_ip(ip_str: str) -> bool:
    """Return True if the IP address falls in any private/reserved range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        # Unparseable IP — treat as blocked.
        return True


def validate_outbound_url(url: str) -> None:
    """
    Validate that a URL is safe for the crawler to visit.

    Raises ScraperException if:
    - The scheme is not http or https
    - The hostname resolves to a private/reserved IP address
    - DNS resolution fails

    This MUST be called before every outbound request in the crawler.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        raise ScraperException(f"SSRF guard: unparseable URL: {url!r}")

    # Reject non-http/https schemes (file://, ftp://, gopher://, etc.)
    if parsed.scheme not in ('http', 'https'):
        raise ScraperException(
            f"SSRF guard: rejected non-HTTP scheme '{parsed.scheme}' in URL: {url!r}"
        )

    hostname = parsed.hostname
    if not hostname:
        raise ScraperException(f"SSRF guard: no hostname in URL: {url!r}")

    # Reject if it looks like an IP literal and is private.
    try:
        ip_literal = ipaddress.ip_address(hostname)
        if _is_private_ip(str(ip_literal)):
            raise ScraperException(
                f"SSRF guard: rejected private IP literal {hostname!r} in URL: {url!r}"
            )
        return  # Public IP literal — allow.
    except ValueError:
        pass  # Not an IP literal — proceed to DNS resolution.

    # Resolve hostname and check every returned address.
    try:
        results = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ScraperException(
            f"SSRF guard: DNS resolution failed for {hostname!r}: {exc}"
        ) from exc

    for family, _type, _proto, _canonname, sockaddr in results:
        ip_str = sockaddr[0]
        if _is_private_ip(ip_str):
            logger.warning(
                f"SSRF guard: blocked request to {url!r} — "
                f"{hostname!r} resolved to private IP {ip_str!r}"
            )
            raise ScraperException(
                f"SSRF guard: {hostname!r} resolves to a private IP address ({ip_str}). "
                f"Request blocked to prevent SSRF."
            )

    logger.debug(f"SSRF guard: {url!r} passed validation.")
