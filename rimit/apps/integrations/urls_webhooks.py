"""URL routes for integrations webhooks (no JWT auth)."""
from django.urls import path
from apps.integrations.views import meta_lead_webhook, razorpay_webhook

urlpatterns = [
    path('meta/leads/', meta_lead_webhook, name='meta-lead-webhook'),
    path('razorpay/payments/', razorpay_webhook, name='razorpay-webhook'),
]
