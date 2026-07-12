from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    """
    Authenticate against django.contrib.auth.models.User using email.
    Falls back to username lookup for robustness.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get('username') or kwargs.get('email') or kwargs.get(UserModel.USERNAME_FIELD)
            
        if not username:
            return None

        try:
            # First try looking up by email
            user = UserModel.objects.get(email__iexact=username)
        except UserModel.DoesNotExist:
            try:
                # Fallback to username lookup
                user = UserModel.objects.get(username__iexact=username)
            except UserModel.DoesNotExist:
                # Run default password hasher to prevent timing attacks
                UserModel().set_password(password)
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
