"""
Shared custom exceptions for GovAlert.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class GovAlertException(Exception):
    """Base exception for all GovAlert errors."""
    pass


class ScraperException(GovAlertException):
    """Raised when a portal scrape fails after all retries."""
    pass


class FakePortalException(GovAlertException):
    """Raised when a portal is confirmed fake (trust score < 30)."""
    pass


class TelegramDeliveryException(GovAlertException):
    """Raised when a Telegram message fails to deliver."""
    pass


class AIClassificationException(GovAlertException):
    """Raised when Gemini AI returns an unexpected or malformed response."""
    pass


# ─── DRF API Exceptions ────────────────────────────────────────────────────────

class PortalNotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Portal not found.'
    default_code = 'portal_not_found'


class AgencyNotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Agency not found.'
    default_code = 'agency_not_found'


class UserAlreadyExistsException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A user with this Telegram ID already exists.'
    default_code = 'user_already_exists'


class RateLimitExceededException(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded. Please try again later.'
    default_code = 'rate_limit_exceeded'
