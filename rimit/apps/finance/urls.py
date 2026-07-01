"""URL routes for finance app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.finance.views import PaymentLedgerViewSet

router = DefaultRouter(trailing_slash=False)
router.register('payments', PaymentLedgerViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]
