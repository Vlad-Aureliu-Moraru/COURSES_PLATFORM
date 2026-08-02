from django.contrib import admin, messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.admin import UserAdmin
from apps.accounts.models import User
from apps.courses.admin import EnrollmentAdmin
from apps.courses.models import Course, Enrollment
from apps.payments.admin import PaymentAdmin
from apps.payments.models import Payment


def make_course():
    return Course.objects.create(
        slug='bani-online',
        title='Cursul complet de bani online',
        price_cents=799,
        currency='eur',
    )


def make_superuser(email='admin@test.com', password='StrongPass1'):
    return User.objects.create_superuser(email=email, password=password, username=email)


def make_user(email='buyer@test.com', password='StrongPass1'):
    return User.objects.create_user(email=email, password=password, username=email)


def make_admin_request(user):
    request = RequestFactory().get('/admin/')
    request.user = user
    request.META['HTTP_REFERER'] = '/admin/'
    setattr(request, 'session', {})
    setattr(request, '_messages', FallbackStorage(request))
    return request


def run_action(admin_cls, model, request, queryset, action):
    model_admin = admin_cls(model=model, admin_site=admin.site)
    model_admin.get_actions(request)[action][0](model_admin, request, queryset)
    return [m.message for m in request._messages]


def test_refund_action_marks_refunded_and_revokes(db):
    course = make_course()
    user = make_user()
    payment = Payment.objects.create(
        user=user, course=course, stripe_session_id='cs_paid_1', status='paid'
    )
    Enrollment.objects.create(user=user, course=course, status='active')

    request = make_admin_request(make_superuser())
    run_action(PaymentAdmin, Payment, request, Payment.objects.filter(id=payment.id), 'refund_payments')

    payment.refresh_from_db()
    assert payment.status == 'refunded'
    assert Enrollment.objects.get(user=user, course=course).status == 'revoked'
    assert len(mail.outbox) == 1
    assert 'Rambursare procesată' in mail.outbox[0].subject


def test_refund_action_skips_non_paid(db):
    course = make_course()
    user = make_user()
    pending = Payment.objects.create(
        user=user, course=course, stripe_session_id='cs_pending', status='pending'
    )

    request = make_admin_request(make_superuser())
    messages_list = run_action(
        PaymentAdmin, Payment, request, Payment.objects.filter(id=pending.id), 'refund_payments'
    )

    pending.refresh_from_db()
    assert pending.status == 'pending'
    assert len(mail.outbox) == 0
    assert any('sărit' in m for m in messages_list)


def test_enrollment_grant_and_revoke_actions(db):
    course = make_course()
    user = make_user()
    enrollment = Enrollment.objects.create(user=user, course=course, status='revoked')

    request = make_admin_request(make_superuser())
    run_action(
        EnrollmentAdmin,
        Enrollment,
        request,
        Enrollment.objects.filter(id=enrollment.id),
        'grant_selected',
    )
    enrollment.refresh_from_db()
    assert enrollment.status == 'active'

    run_action(
        EnrollmentAdmin,
        Enrollment,
        request,
        Enrollment.objects.filter(id=enrollment.id),
        'revoke_selected',
    )
    enrollment.refresh_from_db()
    assert enrollment.status == 'revoked'


def test_user_admin_shows_inlines(db):
    make_superuser()
    client = APIClient()
    client.force_login(User.objects.get(is_superuser=True))
    response = client.get(reverse('admin:accounts_user_changelist'))
    assert response.status_code == 200


def test_payment_admin_display_amount(db):
    course = make_course()
    user = make_user()
    payment = Payment.objects.create(
        user=user, course=course, stripe_session_id='cs_paid_2', status='paid'
    )
    admin_inst = PaymentAdmin(model=Payment, admin_site=admin.site)
    assert admin_inst.display_amount(payment) == '7.99 EUR'
