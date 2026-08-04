import base64
from email.message import EmailMessage

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


class GmailAPIBackend(BaseEmailBackend):
    """Send email through the Gmail REST API over port 443 (no SMTP, no domain).

    Auth: OAuth2 refresh token for the Gmail account; access tokens are minted
    on the fly from GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET / GMAIL_REFRESH_TOKEN.
    """

    TOKEN_URL = 'https://oauth2.googleapis.com/token'
    SEND_URL = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'

    def _access_token(self):
        response = requests.post(
            self.TOKEN_URL,
            data={
                'client_id': settings.GMAIL_CLIENT_ID,
                'client_secret': settings.GMAIL_CLIENT_SECRET,
                'refresh_token': settings.GMAIL_REFRESH_TOKEN,
                'grant_type': 'refresh_token',
            },
            timeout=15,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f'Gmail token error {response.status_code}: {response.text[:300]}'
            )
        return response.json()['access_token']

    def _build_raw(self, message):
        from_email = getattr(message, 'from_email', None) or settings.DEFAULT_FROM_EMAIL
        msg = EmailMessage()
        msg['From'] = from_email
        msg['To'] = ', '.join(message.to)
        msg['Subject'] = message.subject
        msg.set_content(message.body)
        for alternative, mime in message.alternatives:
            if mime == 'text/html':
                msg.add_alternative(alternative, subtype='html')
                break
        return base64.urlsafe_b64encode(msg.as_bytes()).decode()

    def _send_message(self, message):
        access_token = self._access_token()
        response = requests.post(
            self.SEND_URL,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            json={'raw': self._build_raw(message)},
            timeout=20,
        )
        if response.status_code >= 400:
            if self.fail_silently:
                return 0
            raise RuntimeError(
                f'Gmail API error {response.status_code}: {response.text[:300]}'
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
