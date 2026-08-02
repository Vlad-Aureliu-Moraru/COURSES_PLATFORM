import pytest
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from apps.accounts.views import LoginThrottle, PasswordResetRequestThrottle, SignupThrottle


@pytest.fixture(autouse=True)
def disable_throttling(settings):
    AnonRateThrottle.rate = '10000/min'
    UserRateThrottle.rate = '10000/min'
    SignupThrottle.rate = '10000/min'
    LoginThrottle.rate = '10000/min'
    PasswordResetRequestThrottle.rate = '10000/min'
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
        key: '10000/min' for key in settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {})
    }
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.STRIPE_SECRET_KEY = 'sk_test_dummy'
    settings.STRIPE_WEBHOOK_SECRET = 'whsec_dummy'
