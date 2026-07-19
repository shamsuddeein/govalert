"""
Custom DRF permission classes for GovAlert.
"""
from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """
    Grants access only to Django superusers (super admins).
    Used for /broadcast and destructive admin operations.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsAdminUser(BasePermission):
    """
    Grants access to Django staff users (admins and super admins).
    Used for portal management, alert verification, user management.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsStaffUser(BasePermission):
    """
    Grants access only to authenticated users with is_staff=True.
    Required for all GovAlert custom admin API endpoints.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)



class IsReadOnly(BasePermission):
    """
    Allows only GET, HEAD, OPTIONS requests.
    Used for public-facing endpoints.
    """
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

    def has_permission(self, request, view):
        return request.method in self.SAFE_METHODS
