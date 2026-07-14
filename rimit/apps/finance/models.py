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


class SubCenterCommission(UUIDModel, TimeStampedModel):
    sub_center = models.ForeignKey('partners.SubCenter', on_delete=models.CASCADE, related_name='commissions')
    course = models.ForeignKey('aggregator.Course', on_delete=models.CASCADE, related_name='sub_center_commissions')
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'sub_center_commissions'
        unique_together = [['sub_center', 'course']]

    def __str__(self):
        return f"{self.sub_center.name} - {self.course.name}: {self.commission_percent}%"


class Invoice(TenantOwnedModel):
    STATUS_UNPAID = 'Unpaid'
    STATUS_PAID = 'Paid'
    STATUS_FAILED = 'Failed'
    STATUS_CANCELLED = 'Cancelled'
    STATUS_CHOICES = [
        (STATUS_UNPAID, 'Unpaid'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sub_center_commission_deducted = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_payable_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNPAID, db_index=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.id} - {self.status}"


class InvoiceLineItem(UUIDModel, TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    student = models.ForeignKey('admissions.Student', on_delete=models.PROTECT, related_name='invoice_line_items')
    course = models.ForeignKey('aggregator.Course', on_delete=models.PROTECT, null=True, blank=True, related_name='invoice_line_items')

    # Locked fee at time of checkout (sum of course fee structures).
    course_fee = models.DecimalField(max_digits=12, decimal_places=2, help_text="Locked total course fee at time of checkout")

    # Net Remittance breakdown — locked at checkout so later config changes cannot mutate the ledger.
    university_share_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    university_share = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_pool = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sub_center_commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sub_center_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rimit_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_payable = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Amount charged to gateway for this line item')

    class Meta:
        db_table = 'invoice_line_items'

    def __str__(self):
        return f"{self.invoice.id} - {self.student.full_name}: {self.course_fee}"


class Transaction(UUIDModel, TimeStampedModel):
    STATUS_SUCCESS = 'Success'
    STATUS_FAILED = 'Failed'
    STATUS_PENDING = 'Pending'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_PENDING, 'Pending'),
    ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='transactions')
    gateway_reference = models.CharField(max_length=200, unique=True, db_index=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)

    class Meta:
        db_table = 'transactions'

    def __str__(self):
        return f"TXN {self.gateway_reference} - {self.amount_paid} ({self.status})"


class UniversityPayoutLedger(TenantOwnedModel):
    university = models.ForeignKey('aggregator.University', on_delete=models.PROTECT, related_name='payout_ledgers', null=True, blank=True)
    transaction = models.ForeignKey('finance.Transaction', on_delete=models.PROTECT, related_name='payout_ledgers', null=True, blank=True)
    
    total_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Reflects Net Payable from checkout")
    rimit_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payable_to_univ = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default='PENDING')

    class Meta:
        db_table = 'university_payout_ledgers'
