from datetime import timedelta
import re

from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import PasswordResetToken, User


def signup_payload(email='test@example.com', password='StrongPass1', password2='StrongPass1', first_name='Test', last_name='User'):
    return {
        'email': email,
        'password': password,
        'password2': password2,
        'first_name': first_name,
        'last_name': last_name,
    }


def test_signup_creates_user_and_returns_tokens(db):
    client = APIClient()
    response = client.post('/api/v1/auth/signup/', signup_payload(), format='json')

    assert response.status_code == 201
    assert response.data['user']['email'] == 'test@example.com'
    assert 'access' in response.data
    assert 'refresh' in response.data
    assert User.objects.filter(email='test@example.com').exists()


def test_signup_duplicate_email_rejected(db):
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


def test_login_success_and_profile(db):
    client = APIClient()
    client.post('/api/v1/auth/signup/', signup_payload(), format='json')

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
    client.post('/api/v1/auth/signup/', signup_payload(), format='json')

    response = client.post(
        '/api/v1/auth/login/',
        {'email': 'test@example.com', 'password': 'WrongPass1'},
        format='json',
    )
    assert response.status_code == 400


def test_account_locked_after_five_failures(db):
    client = APIClient()
    client.post('/api/v1/auth/signup/', signup_payload(), format='json')

    for _ in range(5):
        client.post(
            '/api/v1/auth/login/',
            {'email': 'test@example.com', 'password': 'WrongPass1'},
            format='json',
        )

    user = User.objects.get(email='test@example.com')
    assert user.is_locked

    locked = client.post(
        '/api/v1/auth/login/',
        {'email': 'test@example.com', 'password': 'StrongPass1'},
        format='json',
    )
    assert locked.status_code == 400


def test_password_reset_flow(db, mailoutbox):
    client = APIClient()
    client.post('/api/v1/auth/signup/', signup_payload(), format='json')

    reset_request = client.post(
        '/api/v1/auth/password/reset/', {'email': 'test@example.com'}, format='json'
    )
    assert reset_request.status_code == 200
    assert len(mailoutbox) >= 2  # welcome + reset

    reset_email = mailoutbox[-1]
    token = re.search(r'token-ul de mai jos:\s*\n+\s*([A-Za-z0-9_-]+)', reset_email.body).group(1)

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
