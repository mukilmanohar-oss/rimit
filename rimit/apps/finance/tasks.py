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
            
            # Update student status
            if student.lead_status == Student.LEAD_STATUS_PENDING:
                student.lead_status = Student.LEAD_STATUS_ENROLLED
                student.save(update_fields=['lead_status'])
            
            fee = line_item.course_fee

            # Net Remittance Model:
            # Use the locked breakdown stored on the invoice line item.
            UniversityPayoutLedger.objects.create(
                sub_center_id=invoice.sub_center_id,  # Inherit tenant
                invoice=invoice,
                transaction=txn,
                student=student,
                total_fee=fee,
                university_share=line_item.university_share,
                gross_pool=line_item.gross_pool,
                sub_center_commission=line_item.sub_center_commission,
                rimit_commission=line_item.rimit_commission,
                payable_to_university=line_item.university_share,
                net_payable=line_item.net_payable,
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
