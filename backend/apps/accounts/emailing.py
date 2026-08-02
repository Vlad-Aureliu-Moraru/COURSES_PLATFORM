from django.conf import settings
from django.core.mail import send_mail


def send_welcome_email(email, full_name=None):
    name = full_name or email
    subject = 'Bine ai venit la BaniOnline!'
    message = (
        f'Salut, {name}!\n\n'
        'Contul tău a fost creat cu succes.\n'
        'În curând vei avea acces la cursul complet de bani online.\n\n'
        'Echipa BaniOnline'
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_password_reset_email(email, full_name=None, token=None):
    name = full_name or email
    subject = 'Resetare parolă BaniOnline'
    message = (
        f'Salut, {name}!\n\n'
        'Ai cerut resetarea parolei. Folosește token-ul de mai jos:\n\n'
        f'{token}\n\n'
        'Token-ul expiră în 24 de ore.\n'
        'Dacă nu ai cerut această resetare, ignoră acest mesaj.\n\n'
        'Echipa BaniOnline'
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
