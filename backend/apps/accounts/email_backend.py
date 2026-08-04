import requests

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendHTTPBackend(BaseEmailBackend):
    """Send email through the Resend HTTP API over port 443.

    Used instead of SMTP because cloud VPS IPs are often blocked from
    outbound SMTP (25/465/587) while HTTPS egress remains open.
    """

    API_URL = 'https://api.resend.com/emails'

    def _send_message(self, message):
        api_key = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        if not api_key:
            raise RuntimeError('EMAIL_HOST_PASSWORD (Resend API key) is not configured.')

        from_email = getattr(message, 'from_email', None) or settings.DEFAULT_FROM_EMAIL
        payload = {
            'from': from_email,
            'to': list(message.to),
            'subject': message.subject,
            'text': message.body,
        }

        for alternative, mime in message.alternatives:
            if mime == 'text/html':
                payload['html'] = alternative
                break

        response = requests.post(
            self.API_URL,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=15,
        )
        if response.status_code >= 400:
            if self.fail_silently:
                return 0
            raise RuntimeError(
                f'Resend API error {response.status_code}: {response.text[:300]}'
            )
        return 1

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            try:
                sent += self._send_message(message)
            except Exception:
                if not self.fail_silently:
                    raise
        return sent
