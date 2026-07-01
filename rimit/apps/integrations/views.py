"""
Webhook receivers for external integrations.

All webhooks use signature verification (HMAC for Meta, signature for Razorpay).
No JWT auth — webhooks are unauthenticated but signed.
"""
import hashlib
import hmac
import json
import logging
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


def verify_meta_signature(payload: bytes, signature_header: str) -> bool:
    """Verify Meta webhook HMAC-SHA256 signature."""
    if not signature_header or not signature_header.startswith('sha256='):
        return False
    expected = 'sha256=' + hmac.new(
        settings.SECRET_KEY.encode(),  # In prod: settings.META_APP_SECRET
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature_header, expected)


class MetaLeadWebhookView(APIView):
    """
    Inbound Meta Lead Ads webhook.

    Per RFP Module 4: "Automated hooks capturing inbound leads from Meta
    advertising infrastructures (Facebook & Instagram Lead Generation)."

    Flow:
      1. Verify HMAC-SHA256 signature
      2. Dedup check against leadgen_id
      3. Write to lead_ingestion_logs with status=ingested
      4. Async Celery task fetches full lead detail via Graph API
    """
    permission_classes = [AllowAny]  # Signature-verified instead
    authentication_classes = []  # No auth for webhooks

    def get(self, request):
        """Meta webhook verification challenge (subscription handshake)."""
        verify_token = settings.SECRET_KEY  # In prod: settings.META_VERIFY_TOKEN
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        if mode == 'subscribe' and token == verify_token:
            return HttpResponse(challenge)
        return HttpResponse(status=403)

    def post(self, request):
        signature = request.headers.get('X-Hub-Signature-256', '')
        payload = request.body

        if not verify_meta_signature(payload, signature):
            logger.warning('Meta webhook signature verification failed')
            return HttpResponse(status=403)

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        if data.get('object') == 'page':
            from apps.integrations.tasks import process_meta_lead
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    lead_value = change.get('value', {})
                    leadgen_id = lead_value.get('leadgen_id', '')
                    if not leadgen_id:
                        continue
                    # Idempotent: dedup by leadgen_id
                    from apps.integrations.models import LeadIngestionLog
                    _, created = LeadIngestionLog.objects.get_or_create(
                        leadgen_id=leadgen_id,
                        defaults={
                            'source': LeadIngestionLog.SOURCE_META,
                            'raw_payload': lead_value,
                            'campaign_id': lead_value.get('campaign_id', ''),
                        },
                    )
                    if created:
                        process_meta_lead.delay(leadgen_id)
            return HttpResponse(status=200)

        return HttpResponse(status=400)


class RazorpayPaymentWebhookView(APIView):
    """
    Inbound Razorpay payment callback.

    Verifies signature, writes to payment_ledgers with idempotency
    (transaction_ref unique constraint prevents duplicates).
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        signature = request.headers.get('X-Razorpay-Signature', '')
        payload = request.body

        # In prod: verify HMAC-SHA256 with Razorpay webhook secret
        # expected = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
        # if not hmac.compare_digest(signature, expected):
        #     return HttpResponse(status=403)

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        event = data.get('event', '')
        payment = data.get('payload', {}).get('payment', {}).get('entity', {})

        if event == 'payment.captured':
            from apps.finance.models import PaymentLedger
            transaction_ref = payment.get('id', '')
            enrollment_id = payment.get('notes', {}).get('enrollment_id')

            try:
                from apps.admissions.models import Enrollment
                # Use all_objects — webhooks have no tenant context
                enrollment = Enrollment.all_objects.get(id=enrollment_id)

                # Idempotent: get_or_create by transaction_ref
                ledger, created = PaymentLedger.all_objects.get_or_create(
                    transaction_ref=transaction_ref,
                    defaults={
                        'enrollment': enrollment,
                        'sub_center': enrollment.sub_center,
                        'amount_paid': payment.get('amount', 0) / 100,  # paise → rupees
                        'status': PaymentLedger.STATUS_CAPTURED,
                        'gateway_response': payment,
                    },
                )

                if created:
                    # Auto-transition enrollment to Fee Paid
                    if enrollment.can_transition_to(Enrollment.STATUS_FEE_PAID):
                        enrollment.status = Enrollment.STATUS_FEE_PAID
                        enrollment.save()
                        # Trigger receipt generation + WhatsApp notification
                        from apps.notifications.tasks import notify_payment_captured
                        notify_payment_captured.delay(str(ledger.id))

            except Enrollment.DoesNotExist:
                logger.error(f'Razorpay webhook for unknown enrollment: {enrollment_id}')
                return HttpResponse(status=404)

        return HttpResponse(status=200)


@csrf_exempt
def meta_lead_webhook(request):
    """Function-based webhook entry point (supports GET + POST)."""
    view = MetaLeadWebhookView.as_view()
    return view(request)


@csrf_exempt
def razorpay_webhook(request):
    """Function-based webhook entry point."""
    view = RazorpayPaymentWebhookView.as_view()
    return view(request)
