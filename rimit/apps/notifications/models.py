"""Notifications app: log table + Celery tasks."""
import uuid
from django.db import models
from apps.common.models import UUIDModel, TimeStampedModel


class NotificationLog(UUIDModel, TimeStampedModel):
    """
    Outbound notification log (partitioned by created_at in prod).

    Per dbschema.md:
      - id (UUID, PK)
      - recipient (VARCHAR)        phone or email
      - channel (VARCHAR)          whatsapp | sms | email
      - template_id (VARCHAR)      e.g., 'enrollment_applied'
      - delivery_status (VARCHAR)  queued | sent | failed | delivered
      - created_at (TIMESTAMP)
    """
    CHANNEL_WHATSAPP = 'whatsapp'
    CHANNEL_SMS = 'sms'
    CHANNEL_EMAIL = 'email'
    CHANNEL_CHOICES = [
        (CHANNEL_WHATSAPP, 'WhatsApp'),
        (CHANNEL_SMS, 'SMS'),
        (CHANNEL_EMAIL, 'Email'),
    ]

    STATUS_QUEUED = 'queued'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_DELIVERED = 'delivered'
    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_DELIVERED, 'Delivered'),
    ]

    recipient = models.CharField(max_length=200, db_index=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, db_index=True)
    template_id = models.CharField(max_length=100, db_index=True)
    context_data = models.JSONField(default=dict, blank=True)
    message_body = models.TextField(blank=True)
    delivery_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED, db_index=True)
    external_message_id = models.CharField(max_length=200, blank=True, db_index=True,
                                            help_text='WhatsApp message_id / SES message_id for idempotency')
    error_msg = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)

    # Optional: link to enrollment for traceability
    related_enrollment = models.ForeignKey(
        'admissions.Enrollment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications',
    )

    class Meta:
        db_table = 'notification_logs'
        indexes = [
            models.Index(fields=['channel', 'delivery_status']),
            models.Index(fields=['template_id']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.channel} → {self.recipient} ({self.template_id}, {self.delivery_status})"
