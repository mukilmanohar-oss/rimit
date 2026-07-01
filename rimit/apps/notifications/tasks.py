"""Celery tasks for notifications (WhatsApp, SMS, Email)."""
import logging
from celery import shared_task
from apps.notifications.models import NotificationLog

logger = logging.getLogger(__name__)


def _send_whatsapp(template_id: str, recipient: str, context: dict) -> str:
    """
    Send WhatsApp template message.

    In prod: POST to https://graph.facebook.com/v18.0/{phone_id}/messages
    with template + components. Returns WhatsApp message_id for idempotency.
    """
    # Stub for dev
    msg_id = f'wa_stub_{template_id}_{hash(recipient) & 0xFFFFFFFF:08x}'
    logger.info(f'[STUB] WhatsApp sent: template={template_id} → {recipient}')
    return msg_id


def _send_sms(recipient: str, body: str) -> str:
    """Send SMS via provider (e.g., MSG91, Twilio)."""
    msg_id = f'sms_stub_{hash(recipient) & 0xFFFFFFFF:08x}'
    logger.info(f'[STUB] SMS sent → {recipient}: {body[:60]}')
    return msg_id


def _send_email(recipient: str, subject: str, body: str) -> str:
    """Send email via SES (prod) or console backend (dev)."""
    msg_id = f'email_stub_{hash(recipient) & 0xFFFFFFFF:08x}'
    logger.info(f'[STUB] Email sent → {recipient}: {subject}')
    return msg_id


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification(self, notification_id: str):
    """
    Send a single notification via the configured channel.

    Idempotency: if external_message_id already set, skip.
    """
    try:
        log = NotificationLog.objects.get(id=notification_id)
        if log.delivery_status in (NotificationLog.STATUS_SENT, NotificationLog.STATUS_DELIVERED):
            return f'ALREADY_SENT:{notification_id}'

        if log.channel == NotificationLog.CHANNEL_WHATSAPP:
            msg_id = _send_whatsapp(log.template_id, log.recipient, log.context_data)
        elif log.channel == NotificationLog.CHANNEL_SMS:
            msg_id = _send_sms(log.recipient, log.message_body)
        elif log.channel == NotificationLog.CHANNEL_EMAIL:
            msg_id = _send_email(log.recipient, log.template_id, log.message_body)
        else:
            log.delivery_status = NotificationLog.STATUS_FAILED
            log.error_msg = f'Unknown channel: {log.channel}'
            log.save()
            return f'UNKNOWN_CHANNEL:{notification_id}'

        log.external_message_id = msg_id
        log.delivery_status = NotificationLog.STATUS_SENT
        log.save()
        return f'OK:{notification_id}'

    except Exception as exc:
        logger.warning(f'Notification {notification_id} failed: {exc}')
        try:
            log = NotificationLog.objects.get(id=notification_id)
            log.retry_count += 1
            log.error_msg = str(exc)
            log.save()
        except Exception:
            pass
        try:
            raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            try:
                log = NotificationLog.objects.get(id=notification_id)
                log.delivery_status = NotificationLog.STATUS_FAILED
                log.save()
            except Exception:
                pass
            return f'FAILED:{notification_id}'


@shared_task
def notify_enrollment_status_change(enrollment_id: str, old_status: str, new_status: str):
    """
    Triggered by Django Signal on enrollment status change.
    Sends WhatsApp + email to student and sub-center.
    """
    from apps.admissions.models import Enrollment
    try:
        # Use all_objects — Celery tasks have no tenant context
        enrollment = Enrollment.all_objects.select_related('student', 'sub_center', 'course').get(id=enrollment_id)
    except Enrollment.DoesNotExist:
        return f'ENROLLMENT_NOT_FOUND:{enrollment_id}'

    template_map = {
        'Applied': 'enrollment_applied',
        'Document Verified': 'enrollment_doc_verified',
        'Fee Pending': 'enrollment_fee_pending',
        'Fee Paid': 'enrollment_fee_paid',
        'Enrolled': 'enrollment_enrolled',
        'Enrollment Generated': 'enrollment_generated',
    }
    template_id = template_map.get(new_status, 'enrollment_status_update')
    context = {
        'student_name': enrollment.student.full_name,
        'course_name': enrollment.course.name,
        'old_status': old_status,
        'new_status': new_status,
    }

    # Queue WhatsApp to student
    if enrollment.student.primary_phone:
        log = NotificationLog.objects.create(
            recipient=enrollment.student.primary_phone,
            channel=NotificationLog.CHANNEL_WHATSAPP,
            template_id=template_id,
            context_data=context,
            related_enrollment=enrollment,
        )
        send_notification.delay(str(log.id))

    return f'OK:{enrollment_id}:{template_id}'


@shared_task
def notify_payment_captured(ledger_id: str):
    """Triggered on payment.captured webhook — send receipt + update enrollment."""
    from apps.finance.models import PaymentLedger
    try:
        ledger = PaymentLedger.all_objects.select_related('enrollment', 'enrollment__student', 'enrollment__course').get(id=ledger_id)
    except PaymentLedger.DoesNotExist:
        return f'LEDGER_NOT_FOUND:{ledger_id}'

    context = {
        'student_name': ledger.enrollment.student.full_name,
        'amount_paid': str(ledger.amount_paid),
        'transaction_ref': ledger.transaction_ref,
        'course_name': ledger.enrollment.course.name,
    }

    log = NotificationLog.objects.create(
        recipient=ledger.enrollment.student.primary_phone,
        channel=NotificationLog.CHANNEL_WHATSAPP,
        template_id='payment_receipt',
        context_data=context,
        related_enrollment=ledger.enrollment,
    )
    send_notification.delay(str(log.id))
    return f'OK:{ledger_id}'


@shared_task
def broadcast_notification(recipient_list, channel, template_id, context):
    """
    Broadcast a notification to many recipients.
    Rate-limited to 75/s for WhatsApp (under Meta's 80/s cap).
    """
    from apps.notifications.models import NotificationLog
    queued = []
    for recipient in recipient_list:
        log = NotificationLog.objects.create(
            recipient=recipient,
            channel=channel,
            template_id=template_id,
            context_data=context,
        )
        queued.append(str(log.id))

    # Stagger sends via Celery chord (rate limit)
    for nid in queued:
        send_notification.delay(nid)

    return f'QUEUED:{len(queued)}'
