from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def _wrap_html(content_html):
    return f"""<!DOCTYPE html>
<html lang="ro">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background-color:#ffffff;border-radius:16px;border:1px solid #e2e8f0;overflow:hidden;">
          <tr>
            <td style="background:linear-gradient(135deg,#4f46e5,#4338ca);padding:28px 32px;">
              <p style="margin:0;font-size:22px;font-weight:bold;color:#ffffff;">Bani<span style="color:#a5b4fc;">Online</span></p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              {content_html}
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px 28px;border-top:1px solid #e2e8f0;">
              <p style="margin:0;font-size:12px;color:#64748b;">
                <a href="{settings.SITE_URL}" style="color:#4f46e5;">{settings.SITE_URL}</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _send_html_email(email, subject, text_body, html_body):
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    message.attach_alternative(html_body, 'text/html')
    message.send()


def send_welcome_email(email, full_name=None):
    name = full_name or email
    subject = 'Bine ai venit la BaniOnline!'
    text_body = (
        f'Salut, {name}!\n\n'
        'Contul tău a fost creat cu succes.\n'
        'În curând vei avea acces la cursul complet de bani online.\n\n'
        'Echipa BaniOnline'
    )
    html_body = _wrap_html(
        f'<h1 style="margin:0 0 8px;font-size:20px;color:#0f172a;">Bine ai venit!</h1>'
        f'<p style="margin:0;font-size:15px;color:#334155;line-height:1.6;">'
        f'Salut, <strong>{name}</strong>!<br>'
        f'Contul tău a fost creat cu succes.<br>'
        f'În curând vei avea acces la cursul complet de bani online.</p>'
        f'<p style="margin:16px 0 0;font-size:15px;color:#334155;line-height:1.6;">'
        f'<a href="{settings.SITE_URL}/curs" style="color:#4f46e5;">Vezi cursul →</a></p>'
    )
    _send_html_email(email, subject, text_body, html_body)


def send_password_reset_email(email, full_name=None, token=None):
    name = full_name or email
    reset_url = f'{settings.SITE_URL}/reset-password-confirm?token={token}'
    subject = 'Resetare parolă BaniOnline'
    text_body = (
        f'Salut, {name}!\n\n'
        'Ai cerut resetarea parolei. Accesează link-ul de mai jos pentru a-ți seta o parolă nouă:\n\n'
        f'{reset_url}\n\n'
        'Link-ul expiră în 24 de ore.\n'
        'Dacă nu ai cerut această resetare, ignoră acest mesaj.\n\n'
        'Echipa BaniOnline'
    )
    html_body = _wrap_html(
        f'<h1 style="margin:0 0 8px;font-size:20px;color:#0f172a;">Resetare parolă</h1>'
        f'<p style="margin:0;font-size:15px;color:#334155;line-height:1.6;">'
        f'Salut, <strong>{name}</strong>!<br>'
        f'Ai cerut resetarea parolei. Apasă pe butonul de mai jos pentru a-ți seta o parolă nouă:</p>'
        f'<p style="margin:24px 0 0;">'
        f'<a href="{reset_url}" style="display:inline-block;background-color:#4f46e5;color:#ffffff;'
        f'text-decoration:none;font-weight:bold;padding:12px 24px;border-radius:8px;">Resetează parola</a>'
        f'</p>'
        f'<p style="margin:16px 0 0;font-size:13px;color:#64748b;">Link-ul expiră în 24 de ore.<br>'
        f'Dacă nu ai cerut această resetare, ignoră acest mesaj.</p>'
    )
    _send_html_email(email, subject, text_body, html_body)
