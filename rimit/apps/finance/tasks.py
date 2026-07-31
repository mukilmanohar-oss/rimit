from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from apps.finance.models import Transaction, UniversityPayoutLedger, Invoice
from apps.admissions.models import Student

@shared_task
def process_ledger_settlement(transaction_id):
    """
    Called asynchronously when a payment webhook succeeds.
    1. Updates student status to ENROLLED.
    2. Calculates commission rules.
    3. Creates payout ledgers.
    """
    try:
        txn = Transaction.objects.select_related('invoice').get(id=transaction_id)
    except Transaction.DoesNotExist:
        return
        
    invoice = txn.invoice
    
    with transaction.atomic():
        for line_item in invoice.line_items.select_related('student', 'student__course'):
            student = line_item.student
            course = getattr(line_item, 'course', None) or student.course
            
            # Check if this invoice is a repayment invoice
            is_repayment = False
            enrollment = line_item.enrollment
            if enrollment:
                from apps.finance.models import PaymentLedger
                is_repayment = PaymentLedger.all_objects.filter(
                    enrollment=enrollment,
                    status=PaymentLedger.STATUS_CAPTURED
                ).exclude(transaction_ref=txn.gateway_reference).exists()

            # Update student status (only for initial payment)
            if not is_repayment:
                if student.lead_status == Student.LEAD_STATUS_PENDING:
                    student.lead_status = Student.LEAD_STATUS_ENROLLED
                    student.save(update_fields=['lead_status'])

            # Net Remittance Model:
            # Use the correct payout fields based on the latest models schema.
            UniversityPayoutLedger.objects.create(
                sub_center_id=invoice.sub_center_id,  # Inherit tenant
                university=course.university,
                transaction=txn,
                total_collected=line_item.net_payable,
                rimit_commission=line_item.rimit_commission,
                payable_to_univ=line_item.university_share,
                status='PENDING'
            )
            
            # Trigger PDF receipt (mocked)
            # generate_receipt_pdf.delay(student.id)

@shared_task
def cancel_stale_invoices():
    """
    Cron job: Cancels UNPAID invoices older than 24h.
    """
    cutoff = timezone.now() - timedelta(hours=24)
    stale_invoices = Invoice.objects.filter(status=Invoice.STATUS_UNPAID, created_at__lt=cutoff)
    
    with transaction.atomic():
        for invoice in stale_invoices:
            invoice.status = Invoice.STATUS_CANCELLED
            invoice.save(update_fields=['status'])
            # Note: Lead status remains 'Pending Payment' so the sub-center can retry later.
