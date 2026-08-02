import shutil

from django.conf import settings
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    data = {'status': 'ok'}

    try:
        connection.ensure_connection()
        data['database'] = 'ok'
    except Exception:
        data['database'] = 'error'
        data['status'] = 'degraded'

    data['redis'] = 'not_configured'

    try:
        latest = MigrationRecorder.Migration.objects.filter(applied__isnull=False).order_by('-applied').first()
        data['last_migration'] = latest.applied.isoformat() if latest else None
    except Exception:
        data['last_migration'] = None

    try:
        total, used, free = shutil.disk_usage(settings.BASE_DIR)
        data['disk_usage_percent'] = round(used / total * 100, 1)
    except Exception:
        data['disk_usage_percent'] = None

    return Response(data)
