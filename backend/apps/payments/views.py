from django.conf import settings

from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from apps.courses.models import Course

from .models import Payment
from .serializers import PaymentSerializer
from .services import create_checkout_session, handle_webhook_event


class CheckoutThrottle(AnonRateThrottle):
    scope = 'checkout'


class CheckoutView(views.APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [CheckoutThrottle]

    def post(self, request):
        slug = request.data.get('course', 'bani-online')
        try:
            course = Course.objects.get(slug=slug, is_published=True)
        except Course.DoesNotExist:
            return Response(
                {'detail': 'Curs inexistent.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        success_url = request.data.get(
            'success_url', settings.SITE_URL + '/success?session_id={CHECKOUT_SESSION_ID}'
        )
        cancel_url = request.data.get('cancel_url', '')

        try:
            session, _ = create_checkout_session(
                request.user, course, success_url, cancel_url
            )
        except Exception:
            return Response(
                {'detail': 'Plata nu poate fi inițiată. Încearcă mai târziu.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'checkout_url': session['url']})


class WebhookThrottle(AnonRateThrottle):
    scope = 'payment_webhook'


class PaymentWebhookView(views.APIView):
    permission_classes = [AllowAny]
    throttle_classes = [WebhookThrottle]
    authentication_classes = []

    def post(self, request):
        if not settings.STRIPE_WEBHOOK_SECRET:
            return Response(status=status.HTTP_403_FORBIDDEN)

        payload = request.body
        sig = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        if not sig:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            handle_webhook_event(payload, sig)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class PaymentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
