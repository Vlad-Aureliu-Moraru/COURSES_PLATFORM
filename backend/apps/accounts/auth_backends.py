from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache

from .models import User


def _client_ip(request):
    if request is None:
        return ''
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


class LockoutAuthBackend(ModelBackend):
    MAX_FAILURES = 10
    WINDOW_SECONDS = 15 * 60

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = (kwargs.get('email') or username or '').strip().lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        ip = _client_ip(request)
        key = f'login-fail:{ip}:{email}'
        failures = cache.get(key, 0)

        if failures >= self.MAX_FAILURES:
            return None

        if user.check_password(password):
            cache.delete(key)
            return user

        failures += 1
        cache.set(key, failures, self.WINDOW_SECONDS)
        return None
