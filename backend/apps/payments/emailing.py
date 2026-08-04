from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from structlog import get_logger

logger = get_logger(__name__)


def _wrap_html(title, content_html):
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
              <h1 style="margin:0 0 8px;font-size:20px;color:#0f172a;">{title}</h1>
              {content_html}
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px 28px;border-top:1px solid #e2e8f0;">
              <p style="margin:0;font-size:12px;color:#64748b;">
                BaniOnline — curs de bani online pentru începători.<br>
                Ai întrebări? Scrie-ne la <a href="mailto:pressync.app@gmail.com" style="color:#4f46e5;">pressync.app@gmail.com</a>.<br>
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


def _btn(href, label):
    return (
        f'<p style="margin:24px 0 0;">'
        f'<a href="{href}" style="display:inline-block;background-color:#4f46e5;color:#ffffff;'
        f'text-decoration:none;font-weight:bold;padding:12px 24px;border-radius:8px;">{label}</a>'
        f'</p>'
    )


def _send_html_email(email, subject, text_body, html_body):
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    message.attach_alternative(html_body, 'text/html')
    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception('email_send_failed', to=email, subject=subject)


def send_payment_confirmation_email(user, payment):
    email = user.email
    name = user.get_full_name() or user.email
    course_title = payment.course.title if payment.course else 'Cursul complet de bani online'
    amount = f'{payment.total:.2f} {payment.currency.upper()}'

    subject = 'Plata a fost confirmată — BaniOnline'
    text_body = (
        f'Salut, {name}!\n\n'
        f'Plata ta de {amount} a fost confirmată.\n'
        f'Ai acces instant la „{course_title}” — toate cele 12 module sunt deblocate.\n\n'
        f'Accesează cursul: {settings.SITE_URL}/curs\n\n'
        'Echipa BaniOnline'
    )

    html_body = _wrap_html(
        'Plata a fost confirmată ✓',
        f'<p style="margin:0;font-size:15px;color:#334155;line-height:1.6;">'
        f'Salut, <strong>{name}</strong>!<br>'
        f'Plata ta de <strong>{amount}</strong> a fost confirmată.</p>'
        f'<p style="margin:16px 0 0;font-size:15px;color:#334155;line-height:1.6;">'
        f'Ai acces instant la <strong>{course_title}</strong> — toate cele 12 module sunt deblocate.</p>'
        f'{_btn(f"{settings.SITE_URL}/curs", "Accesează cursul")}',
    )

    _send_html_email(email, subject, text_body, html_body)
