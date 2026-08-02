from django.urls import path

from .views import CheckoutView, PaymentListView, PaymentWebhookView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='payment-checkout'),
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    path('', PaymentListView.as_view(), name='payment-list'),
]
