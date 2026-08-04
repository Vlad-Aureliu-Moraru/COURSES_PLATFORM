from datetime import timedelta
import hashlib
import re

from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import EmailVerificationCode, PasswordResetToken, User


def signup_payload(email='test@example.com', password='StrongPass1', password2='StrongPass1', first_name='Test', last_name='User'):
    return {
        'email': email,
        'password': password,
        'password2': password2,
        'first_name': first_name,
        'last_name': last_name,
    }


def get_otp_code(user):
    instance = EmailVerificationCode.objects.get(user=user)
    return next(
        f'{i:06d}'
        for i in range(1000000)
        if EmailVerificationCode.hash_code(f'{i:06d}') == instance.code_hash
    )


def signup_and_get_code(client, email='test@example.com'):
    client.post('/api/v1/auth/signup/', signup_payload(email=email), format='json')
    return get_otp_code(User.objects.get(email=email))


def test_signup_creates_inactive_user_sends_otp(db, mailoutbox):
    client = APIClient()
    response = client.post('/api/v1/auth/signup/', signup_payload(), format='json')

    assert response.status_code == 201
    assert response.data['email'] == 'test@example.com'
    assert 'access' not in response.data
    user = User.objects.get(email='test@example.com')
    assert user.is_active is False
    assert len(mailoutbox) == 1
    assert 'Codul tău de verificare' in mailoutbox[0].subject
    assert EmailVerificationCode.objects.filter(user=user).exists()


def test_signup_duplicate_email_rejected(db, mailoutbox):
    client = APIClient()
    client.post('/api/v1/auth/signup/', signup_payload(), format='json')

    response = client.post('/api/v1/auth/signup/', signup_payload(), format='json')
    assert response.status_code == 400


def test_signup_weak_password_rejected(db):
    client = APIClient()
    response = client.post(
        '/api/v1/auth/signup/', signup_payload(password='weak'), format='json'
    )
    assert response.status_code == 400


def test_signup_verify_activates_and_returns_tokens(db, mailoutbox):
    client = APIClient()
    code = signup_and_get_code(client)

    verify = client.post(
        '/api/v1/auth/signup/verify/',
        {'email': 'test@example.com', 'code': code},
        format='json',
    )
    assert verify.status_code == 200
    assert verify.data['user']['email'] == 'test@example.com'
    assert 'access' in verify.data
    assert 'refresh' in verify.data
    user = User.objects.get(email='test@example.com')
    assert user.is_active is True
    assert not EmailVerificationCode.objects.filter(user=user).exists()
    assert len(mailoutbox) == 2  # otp + welcome
    assert 'Bine ai venit' in mailoutbox[-1].subject


def test_signup_verify_wrong_code_rejected(db):
    client = APIClient()
    client.post('/api/v1/auth/signup/', signup_payload(), format='json')

    verify = client.post(
        '/api/v1/auth/signup/verify/',
        {'email': 'test@example.com', 'code': '000000'},
        format='json',
    )
    assert verify.status_code == 400
    assert User.objects.get(email='test@example.com').is_active is False


def test_signup_verify_expired_code_rejected(db):
    client = APIClient()
    client.post('/api/v1/auth/signup/', signup_payload(), format='json')
    user = User.objects.get(email='test@example.com')
    EmailVerificationCode.objects.filter(user=user).update(
        expires_at=timezone.now() - timedelta(minutes=1)
    )
    code = get_otp_code(user)

    verify = client.post(
        '/api/v1/auth/signup/verify/',
        {'email': 'test@example.com', 'code': code},
        format='json',
    )
    assert verify.status_code == 400
    assert User.objects.get(email='test@example.com').is_active is False


def test_signup_resend_reissues_code(db, mailoutbox):
    client = APIClient()
    client.post('/api/v1/auth/signup/', signup_payload(), format='json')
    user = User.objects.get(email='test@example.com')
    original_hash = EmailVerificationCode.objects.get(user=user).code_hash

    resend = client.post(
        '/api/v1/auth/signup/resend/', {'email': 'test@example.com'}, format='json'
    )
    assert resend.status_code == 200
    assert EmailVerificationCode.objects.get(user=user).code_hash != original_hash
    assert len(mailoutbox) == 2  # original otp + resent


def test_inactive_email_reusable_after_24h(db):
    client = APIClient()
    client.post('/api/v1/auth/signup/', signup_payload(), format='json')
    user = User.objects.get(email='test@example.com')
    User.objects.filter(pk=user.pk).update(date_joined=timezone.now() - timedelta(hours=25))

    response = client.post('/api/v1/auth/signup/', signup_payload(), format='json')
    assert response.status_code == 201
    assert User.objects.filter(email='test@example.com', is_active=False).count() == 1


def test_login_blocked_until_verified(db):
    client = APIClient()
    client.post('/api/v1/auth/signup/', signup_payload(), format='json')

    login = client.post(
        '/api/v1/auth/login/',
        {'email': 'test@example.com', 'password': 'StrongPass1'},
        format='json',
    )
    assert login.status_code == 400

    code = signup_and_get_code(client, email='test@example.com')
    client.post(
        '/api/v1/auth/signup/verify/',
        {'email': 'test@example.com', 'code': code},
        format='json',
    )
    login = client.post(
        '/api/v1/auth/login/',
        {'email': 'test@example.com', 'password': 'StrongPass1'},
        format='json',
    )
    assert login.status_code == 200
    access = login.data['access']

    profile = client.get('/api/v1/auth/profile/', HTTP_AUTHORIZATION=f'Bearer {access}')
    assert profile.status_code == 200
    assert profile.data['email'] == 'test@example.com'


def test_profile_requires_auth(db):
    client = APIClient()
    assert client.get('/api/v1/auth/profile/').status_code == 401


def test_login_wrong_password(db):
    client = APIClient()
    code = signup_and_get_code(client)
    client.post(
        '/api/v1/auth/signup/verify/',
        {'email': 'test@example.com', 'code': code},
        format='json',
    )

    response = client.post(
        '/api/v1/auth/login/',
        {'email': 'test@example.com', 'password': 'WrongPass1'},
        format='json',
    )
    assert response.status_code == 400


def test_login_throttled_after_failures_from_same_ip(db):
    client = APIClient()
    code = signup_and_get_code(client)
    client.post(
        '/api/v1/auth/signup/verify/',
        {'email': 'test@example.com', 'code': code},
        format='json',
    )

    for _ in range(12):
        client.post(
            '/api/v1/auth/login/',
            {'email': 'test@example.com', 'password': 'WrongPass1'},
            format='json',
        )

    response = client.post(
        '/api/v1/auth/login/',
        {'email': 'test@example.com', 'password': 'StrongPass1'},
        format='json',
    )
    assert response.status_code == 429 or response.status_code == 400


def test_password_reset_flow(db, mailoutbox):
    client = APIClient()
    code = signup_and_get_code(client)
    client.post(
        '/api/v1/auth/signup/verify/',
        {'email': 'test@example.com', 'code': code},
        format='json',
    )

    reset_request = client.post(
        '/api/v1/auth/password/reset/', {'email': 'test@example.com'}, format='json'
    )
    assert reset_request.status_code == 200
    assert len(mailoutbox) >= 3  # otp + welcome + reset

    reset_email = mailoutbox[-1]
    token = re.search(r'/reset-password-confirm\?token=([A-Za-z0-9_-]+)', reset_email.body).group(1)

    user = User.objects.get(email='test@example.com')
    assert PasswordResetToken.objects.filter(user=user).exists()

    reset_confirm = client.post(
        '/api/v1/auth/password/reset/confirm/',
        {'token': token, 'new_password': 'NewPass123', 'new_password2': 'NewPass123'},
        format='json',
    )
    assert reset_confirm.status_code == 200

    user.refresh_from_db()
    assert user.check_password('NewPass123')
