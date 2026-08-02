from datetime import timedelta

from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

from .models import User


class LockoutAuthBackend(ModelBackend):
    LOCKOUT_THRESHOLD = 5
    LOCKOUT_DURATION = timedelta(minutes=15)

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email') or username
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        if user.is_locked:
            return None

        if user.check_password(password):
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=['failed_login_attempts', 'locked_until'])
            return user

        user.failed_login_attempts += 1
        if user.failed_login_attempts >= self.LOCKOUT_THRESHOLD:
            user.locked_until = timezone.now() + self.LOCKOUT_DURATION
        user.save(update_fields=['failed_login_attempts', 'locked_until'])
        return None
