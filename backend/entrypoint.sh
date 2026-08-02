#!/bin/sh
set -e

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.production}

# Migrations + static files must run with write access to /app/staticfiles (volume).
if [ "$(id -u)" = "0" ]; then
    mkdir -p /app/staticfiles /app/media
    chown -R appuser:appuser /app/staticfiles /app/media
    python manage.py migrate --noinput --fake-initial
    python manage.py collectstatic --noinput --clear
    exec gosu appuser "$@"
fi

python manage.py migrate --noinput --fake-initial
python manage.py collectstatic --noinput --clear
exec "$@"
