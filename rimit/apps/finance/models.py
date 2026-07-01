"""
Finance app: payment_ledgers model + financial dashboard endpoints.

Per dbschema.md:
  - payment_ledgers: id (UUID, PK), enrollment_id (FK), amount_paid (DECIMAL),
                     transaction_ref (VARCHAR, UNIQUE), status (VARCHAR)
"""
import uuid
from django.db import models
from apps.common.models import UUIDModel, TimeStampedModel, TenantOwnedModel


class PaymentLedger(TenantOwnedModel):
    """
    Payment ledger entry. Idempotent on transaction_ref.

    Per dbschema.md:
      - id (UUID, PK)
      - enrollment_id (FK)
      - amount_paid (DECIMAL)
      - transaction_ref (VARCHAR, UNIQUE)
      - status (VARCHAR)
    """
    STATUS_PENDING = 'pending'
    STATUS_CAPTURED = 'captured'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CAPTURED, 'Captured'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    enrollment = models.ForeignKey(
        'admissions.Enrollment', on_delete=models.PROTECT, related_name='payments'
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_ref = models.CharField(max_length=200, unique=True, db_index=True,
                                        help_text='Gateway transaction ID; unique for idempotency')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    gateway = models.CharField(max_length=50, default='razorpay')
    gateway_response = models.JSONField(default=dict, blank=True)
    receipt_uri = models.URLField(blank=True, help_text='MinIO URI of generated receipt PDF')

    class Meta:
        db_table = 'payment_ledgers'
        indexes = [
            models.Index(fields=['enrollment', 'status']),
            models.Index(fields=['sub_center', 'status']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.enrollment} - {self.amount_paid} INR ({self.status})"
