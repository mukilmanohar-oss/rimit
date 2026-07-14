"""URL routes for finance app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.finance.views import PaymentLedgerViewSet, BatchCheckoutView, PaymentWebhookView

router = DefaultRouter(trailing_slash=False)
router.register('payments', PaymentLedgerViewSet, basename='payment')

urlpatterns = [
    path('checkout/batch/', BatchCheckoutView.as_view(), name='batch-checkout'),
    path('checkout/batch', BatchCheckoutView.as_view(), name='batch-checkout-noslash'),
    path('webhooks/payment/', PaymentWebhookView.as_view(), name='payment-webhook'),
    path('webhooks/payment', PaymentWebhookView.as_view(), name='payment-webhook-noslash'),
    path('', include(router.urls)),
]
