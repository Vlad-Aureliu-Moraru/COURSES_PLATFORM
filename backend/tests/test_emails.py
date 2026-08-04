from unittest.mock import patch

from django.core import mail
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment
from apps.payments.models import Payment


def make_course():
    return Course.objects.create(
        slug='bani-online',
        title='Cursul complet de bani online',
        price_cents=799,
        currency='eur',
    )


def make_user(email='buyer@test.com', password='StrongPass1'):
    return User.objects.create_user(email=email, password=password, username=email)


def webhook_event(event):
    client = APIClient()
    with patch(
        'apps.payments.services.stripe.Webhook.construct_event', return_value=event
    ):
        return client.post(
            '/api/v1/payments/webhook/',
            'payload',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=sig',
        )


def test_signup_sends_otp_email(db, mailoutbox):
    client = APIClient()
    response = client.post(
        '/api/v1/auth/signup/',
        {'email': 'new@test.com', 'password': 'StrongPass1', 'password2': 'StrongPass1'},
        format='json',
    )
    assert response.status_code == 201
    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == ['new@test.com']
    assert 'Codul tău de verificare' in sent.subject
    assert len(sent.alternatives) == 1
    assert sent.alternatives[0][1] == 'text/html'


def test_signup_verify_sends_welcome_email(db, mailoutbox):
    from apps.accounts.models import EmailVerificationCode, User

    client = APIClient()
    client.post(
        '/api/v1/auth/signup/',
        {'email': 'new@test.com', 'password': 'StrongPass1', 'password2': 'StrongPass1'},
        format='json',
    )
    user = User.objects.get(email='new@test.com')
    instance = EmailVerificationCode.objects.get(user=user)
    code = next(
        f'{i:06d}'
        for i in range(1000000)
        if EmailVerificationCode.hash_code(f'{i:06d}') == instance.code_hash
    )
    response = client.post(
        '/api/v1/auth/signup/verify/',
        {'email': 'new@test.com', 'code': code},
        format='json',
    )
    assert response.status_code == 200
    assert len(mail.outbox) == 2
    welcome = mail.outbox[-1]
    assert welcome.to == ['new@test.com']
    assert 'Bine ai venit' in welcome.subject
    assert len(welcome.alternatives) == 1
    assert welcome.alternatives[0][1] == 'text/html'


def test_payment_completed_sends_confirmation_email(db):
    course = make_course()
    user = make_user()
    Payment.objects.create(
        user=user, course=course, stripe_session_id='cs_test_123', status='pending'
    )

    response = webhook_event({
        'type': 'checkout.session.completed',
        'data': {'object': {'id': 'cs_test_123', 'payment_status': 'paid', 'total_details': {'amount_tax': 0}}},
    })

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == ['buyer@test.com']
    assert 'Plata a fost confirmată' in sent.subject
    assert '7.99 EUR' in sent.body
    assert 'Cursul complet de bani online' in sent.body
    assert 'text/html' in [alt[1] for alt in sent.alternatives]
    assert Enrollment.objects.filter(user=user, course=course, status='active').exists()


def test_email_failure_does_not_break_webhook(db):
    course = make_course()
    user = make_user()
    Payment.objects.create(
        user=user, course=course, stripe_session_id='cs_test_123', status='pending'
    )

    with patch(
        'apps.payments.services.send_payment_confirmation_email',
        side_effect=Exception('SMTP down'),
    ):
        response = webhook_event({
            'type': 'checkout.session.completed',
            'data': {'object': {'id': 'cs_test_123', 'payment_status': 'paid', 'total_details': {'amount_tax': 0}}},
        })

    assert response.status_code == 200
    assert len(mail.outbox) == 0
    assert Enrollment.objects.filter(user=user, course=course, status='active').exists()
