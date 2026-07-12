from django.contrib.admin.forms import AdminAuthenticationForm
from django import forms

class EmailAdminAuthenticationForm(AdminAuthenticationForm):
    """
    Custom admin authentication form that uses email instead of username.
    Uses CharField with EmailInput widget to allow fallback username authentication
    without failing form-level validation.
    """
    username = forms.CharField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True})
    )
