from unittest.mock import patch

from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment
from apps.payments.models import Payment


def make_course():
    return Course.objects.create(
        slug='bani-online',
        title='Curs de test',
        price_cents=799,
        currency='eur',
    )


def make_user(email='buyer@test.com', password='StrongPass1'):
    return User.objects.create_user(email=email, password=password, username=email)


def auth_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_checkout_requires_auth(db):
    client = APIClient()
    response = client.post('/api/v1/payments/checkout/', {}, format='json')
    assert response.status_code == 401


def test_checkout_creates_pending_payment(db):
    course = make_course()
    user = make_user()
    client = auth_client(user)

    session = {
        'id': 'cs_test_123',
        'url': 'https://checkout.stripe.com/c/pay/cs_test_123',
    }

    with patch('apps.payments.services.stripe.checkout.Session.create', return_value=session):
        response = client.post(
            '/api/v1/payments/checkout/',
            {'course': 'bani-online'},
            format='json',
        )

    assert response.status_code == 200
    assert response.data['checkout_url'] == 'https://checkout.stripe.com/c/pay/cs_test_123'

    payment = Payment.objects.get(stripe_session_id='cs_test_123')
    assert payment.user == user
    assert payment.course == course
    assert payment.status == 'pending'
    assert payment.amount_cents == 799


def test_checkout_enables_automatic_tax(db):
    course = make_course()
    user = make_user()
    client = auth_client(user)

    session = {
        'id': 'cs_tax_1',
        'url': 'https://checkout.stripe.com/c/pay/cs_tax_1',
    }

    with patch('apps.payments.services.stripe.checkout.Session.create', return_value=session) as mock:
        response = client.post(
            '/api/v1/payments/checkout/',
            {'course': 'bani-online'},
            format='json',
        )

    assert response.status_code == 200
    assert mock.call_args.kwargs['automatic_tax'] == {'enabled': True}


def test_webhook_rejects_bad_signature(db):
    client = APIClient()
    with patch('apps.payments.services.stripe.Webhook.construct_event', side_effect=Exception('bad sig')):
        response = client.post(
            '/api/v1/payments/webhook/',
            '{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=bad',
        )
    assert response.status_code == 400


def test_webhook_completed_grants_access(db):
    course = make_course()
    user = make_user()
    payment = Payment.objects.create(
        user=user, course=course, stripe_session_id='cs_test_123', status='pending'
    )

    event = {
        'type': 'checkout.session.completed',
        'data': {'object': {'id': 'cs_test_123', 'payment_status': 'paid', 'total_details': {'amount_tax': 0}}},
    }

    client = APIClient()
    with patch(
        'apps.payments.services.stripe.Webhook.construct_event', return_value=event
    ):
        response = client.post(
            '/api/v1/payments/webhook/',
            'payload',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=sig',
        )

    assert response.status_code == 200
    payment.refresh_from_db()
    assert payment.status == 'paid'
    assert Enrollment.objects.filter(user=user, course=course, status='active').exists()


def test_payment_list_own_only(db):
    course = make_course()
    user = make_user()
    other = make_user(email='other@test.com')
    Payment.objects.create(user=user, course=course, stripe_session_id='cs_a', status='paid', amount_cents=799)
    Payment.objects.create(user=other, course=course, stripe_session_id='cs_b', status='paid', amount_cents=799)

    client = auth_client(user)
    response = client.get('/api/v1/payments/')
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['course'] == 'bani-online'
    assert response.data['results'][0]['amount'] == '7.99'
