from django.conf import settings
from django.http import HttpResponseForbidden


class AdminIPAllowlistMiddleware:
    """Allow access to /admin/ only from allowed IPs (env ADMIN_ALLOWED_IPS)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed = {
            ip.strip()
            for ip in (getattr(settings, 'ADMIN_ALLOWED_IPS', '') or '').split(',')
            if ip.strip()
        }

    def __call__(self, request):
        if self.allowed and request.path.startswith('/admin/'):
            ip = self._client_ip(request)
            if ip not in self.allowed:
                return HttpResponseForbidden('Acces interzis.')
        return self.get_response(request)

    @staticmethod
    def _client_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
