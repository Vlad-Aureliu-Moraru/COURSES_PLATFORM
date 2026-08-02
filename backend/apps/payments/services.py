import logging

import stripe
from django.conf import settings

from apps.courses.services import grant_access, revoke_access

from .emailing import send_payment_confirmation_email, send_refund_email
from .models import Payment

logger = logging.getLogger('apps.payments')


def get_stripe():
    return stripe


def create_checkout_session(user, course, success_url, cancel_url=''):
    if not settings.STRIPE_SECRET_KEY:
        raise stripe.error.StripeError('Stripe not configured')

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        mode='payment',
        customer_email=user.email,
        line_items=[{
            'price_data': {
                'currency': course.currency,
                'unit_amount': course.price_cents,
                'product_data': {
                    'name': course.title,
                    'description': course.description[:200],
                },
            },
            'quantity': 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url or settings.SITE_URL + '/pricing/',
        metadata={'user_id': user.id, 'course_id': course.id},
    )

    payment, _ = Payment.objects.get_or_create(
        stripe_session_id=session['id'],
        defaults={
            'user': user,
            'course': course,
            'amount_cents': course.price_cents,
            'currency': course.currency,
        },
    )
    return session, payment


def handle_webhook_event(payload, sig):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    event = stripe.Webhook.construct_event(
        payload, sig, settings.STRIPE_WEBHOOK_SECRET
    )

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        _mark_paid(session)
    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        _mark_refunded(session)
    elif event['type'] == 'charge.refunded':
        session_id = _session_from_charge(event['data']['object'])
        if session_id:
            _mark_refunded({'id': session_id})

    return event


def _mark_paid(session):
    payment = Payment.objects.filter(
        stripe_session_id=session['id'], status='pending'
    ).first()
    if payment is None:
        return
    payment.status = 'paid'
    payment.save(update_fields=['status', 'updated_at'])
    if payment.course_id:
        grant_access(payment.user, payment.course)
    try:
        send_payment_confirmation_email(payment.user, payment)
    except Exception:
        logger.exception('Failed to send payment confirmation email for payment %s', payment.id)


def _mark_refunded(session):
    payment = Payment.objects.filter(
        stripe_session_id=session['id'], status='paid'
    ).first()
    if payment is None:
        return
    refund_payment(payment)


def refund_payment(payment):
    payment.status = 'refunded'
    payment.save(update_fields=['status', 'updated_at'])
    if payment.course_id:
        revoke_access(payment.user, payment.course)
    try:
        send_refund_email(payment.user, payment)
    except Exception:
        logger.exception('Failed to send refund email for payment %s', payment.id)


def _session_from_charge(charge):
    payment_intent = charge.get('payment_intent')
    if not payment_intent:
        return None
    stripe.api_key = settings.STRIPE_SECRET_KEY
    pi = stripe.PaymentIntent.retrieve(payment_intent)
    for s in pi.get('checkout', {}).get('session', {}).values() or []:
        if isinstance(s, dict):
            return s.get('id')
    return None


def user_has_purchased(user, course):
    if user is None or user.is_anonymous:
        return False
    return Payment.objects.filter(
        user=user, course=course, status='paid'
    ).exists()
