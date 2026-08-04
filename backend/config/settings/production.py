from decouple import config
from dj_database_url import parse as db_url

from .base import *

DEBUG = False

SECRET_KEY = config('DJANGO_SECRET_KEY')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

_hosts_raw = config('DJANGO_ALLOWED_HOSTS', default='').strip()
ALLOWED_HOSTS = _hosts_raw.split(',') if _hosts_raw else ['localhost']

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
_csrf_raw = config('CSRF_TRUSTED_ORIGINS', default='').strip()
CSRF_TRUSTED_ORIGINS = _csrf_raw.split(',') if _csrf_raw else []

DATABASES = {
    'default': db_url(
        config('DATABASE_URL', default=''),
        conn_max_age=60,
    ) if config('DATABASE_URL', default='') else {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST'),
        'PORT': config('POSTGRES_PORT'),
    }
}

LOGGING['loggers']['django']['handlers'] = ['json']
LOGGING['loggers']['apps']['handlers'] = ['json']

EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL', default='BaniOnline <onboarding@resend.dev>'
)

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '20/hour',
    'user': '1000/hour',
    'signup': '2/min',
    'signup_verify': '10/min',
    'signup_resend': '2/min',
    'login': '5/min',
    'checkout': '10/min',
    'payment': '10/min',
    'payment_webhook': '10/min',
}

_cors_raw = config('CORS_ALLOWED_ORIGINS', default='').strip()
CORS_ALLOWED_ORIGINS = _cors_raw.split(',') if _cors_raw else []
CSP_CONNECT_SRC = ["'self'"] + CORS_ALLOWED_ORIGINS
