import json
from decimal import Decimal
import pytest
from rest_framework import status
from django.test import Client
from apps.admissions.models import Enrollment, Student
from apps.finance.models import PaymentLedger, Invoice, InvoiceLineItem, Transaction, UniversityPayoutLedger
from apps.aggregator.models import FeeStructure
from apps.partners.models import SubCenterUniversityMapping
from tests.base import BaseAPITestCase
from tests.factories import (
    UniversityFactory, CourseFactory, FeeStructureFactory, StudentFactory, IntakeSessionFactory
)

@pytest.mark.django_db
class TestRepaymentFeature(BaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.session = IntakeSessionFactory(is_active=True, is_fresh_allowed=True)
        self.uni = UniversityFactory()
        self.course = CourseFactory(university=self.uni)
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=self.uni)
        
        # Setup Fee Structure (Tuition = 4000, Reg = 1000, Exam = 3000 -> Total = 8000)
        self.f_tuition = FeeStructureFactory(course=self.course, fee_type=FeeStructure.FEE_TUITION, amount=Decimal('4000.00'), is_active=True)
        self.f_reg = FeeStructureFactory(course=self.course, fee_type=FeeStructure.FEE_REGISTRATION, amount=Decimal('1000.00'), is_active=True)
        self.f_exam = FeeStructureFactory(course=self.course, fee_type=FeeStructure.FEE_EXAM, amount=Decimal('3000.00'), is_active=True)
        
        self.student = StudentFactory(sub_center=self.center_a, course=self.course, session=self.session)
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            session=self.session,
            status=Enrollment.STATUS_APPLIED,
            sub_center=self.center_a
        )

    def test_repayment_calculation_with_registration_fee(self):
        """Verify repayment amount calculation correctly deducts registration fee."""
        Enrollment.all_objects.filter(id=self.enrollment.id).update(status=Enrollment.STATUS_ENROLLMENT_GENERATED)
        self.enrollment.refresh_from_db()
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.get(f'/api/v1/enrollments/{self.enrollment.id}/repayment')
        assert resp.status_code == status.HTTP_200_OK
        assert Decimal(resp.data['course_total_fee']) == Decimal('8000.00')
        assert Decimal(resp.data['registration_fee']) == Decimal('1000.00')
        assert Decimal(resp.data['repayment_amount']) == Decimal('7000.00') # 8000 - 1000 = 7000

    def test_repayment_calculation_missing_registration_fee(self):
        """Verify repayment amount equals total active fees if registration fee is missing."""
        self.f_reg.delete()
        Enrollment.all_objects.filter(id=self.enrollment.id).update(status=Enrollment.STATUS_ENROLLMENT_GENERATED)
        self.enrollment.refresh_from_db()
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.get(f'/api/v1/enrollments/{self.enrollment.id}/repayment')
        assert resp.status_code == status.HTTP_200_OK
        assert Decimal(resp.data['course_total_fee']) == Decimal('7000.00')
        assert Decimal(resp.data['registration_fee']) == Decimal('0.00')
        assert Decimal(resp.data['repayment_amount']) == Decimal('7000.00')

    def test_repayment_calculation_inactive_registration_fee(self):
        """Verify inactive registration fee is not deducted."""
        self.f_reg.is_active = False
        self.f_reg.save()
        Enrollment.all_objects.filter(id=self.enrollment.id).update(status=Enrollment.STATUS_ENROLLMENT_GENERATED)
        self.enrollment.refresh_from_db()
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.get(f'/api/v1/enrollments/{self.enrollment.id}/repayment')
        assert resp.status_code == status.HTTP_200_OK
        assert Decimal(resp.data['course_total_fee']) == Decimal('7000.00')
        assert Decimal(resp.data['registration_fee']) == Decimal('0.00')
        assert Decimal(resp.data['repayment_amount']) == Decimal('7000.00')

    def test_repayment_availability_status_guards(self):
        """Verify repayment is blocked before Enrollment Generated and allowed after."""
        client = self.counselor_client(sub_center=self.center_a)
        
        # Blocked in Applied status
        resp = client.get(f'/api/v1/enrollments/{self.enrollment.id}/repayment')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        
        resp = client.post(f'/api/v1/enrollments/{self.enrollment.id}/repayment_checkout')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        # Allowed in Enrollment Generated status
        Enrollment.all_objects.filter(id=self.enrollment.id).update(status=Enrollment.STATUS_ENROLLMENT_GENERATED)
        self.enrollment.refresh_from_db()
        
        resp = client.get(f'/api/v1/enrollments/{self.enrollment.id}/repayment')
        assert resp.status_code == status.HTTP_200_OK
        
        resp = client.post(f'/api/v1/enrollments/{self.enrollment.id}/repayment_checkout')
        assert resp.status_code == status.HTTP_200_OK

    def test_repayment_checkout_tenant_isolation(self):
        """Verify Center B counselors cannot access or checkout repayments for Center A's enrollment."""
        Enrollment.all_objects.filter(id=self.enrollment.id).update(status=Enrollment.STATUS_ENROLLMENT_GENERATED)
        self.enrollment.refresh_from_db()
        
        client_b = self.counselor_client(sub_center=self.center_b)
        resp = client_b.post(f'/api/v1/enrollments/{self.enrollment.id}/repayment_checkout')
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_successful_repayments_and_webhook_flows(self):
        """Verify successful repayments do not alter status, and create separate ledger records."""
        # 1. Simulate initial payment
        initial_ledger = PaymentLedger.all_objects.create(
            enrollment=self.enrollment,
            sub_center=self.center_a,
            amount_paid=Decimal('8000.00'),
            transaction_ref='initial_ref',
            status=PaymentLedger.STATUS_CAPTURED
        )
        
        # Enrollment status transitions to generated
        Enrollment.all_objects.filter(id=self.enrollment.id).update(
            status=Enrollment.STATUS_ENROLLMENT_GENERATED,
            admission_number='ADM123',
            registration_number='REG456'
        )
        self.enrollment.refresh_from_db()
        
        client = self.counselor_client(sub_center=self.center_a)
        
        # 2. Initiate Repayment checkout
        resp = client.post(f'/api/v1/enrollments/{self.enrollment.id}/repayment_checkout')
        assert resp.status_code == status.HTTP_200_OK
        invoice_id = resp.data['invoice_id']
        
        # 3. Simulate payment capture via PaymentWebhookView success callback
        anon_client = Client()
        resp = anon_client.post(
            '/api/v1/webhooks/payment/',
            json.dumps({
                'invoice_id': invoice_id,
                'status': 'success',
                'gateway_reference': 'repay_ref_001'
            }),
            content_type='application/json'
        )
        assert resp.status_code == status.HTTP_200_OK
        
        # 4. Verify enrollment status and numbers remain unchanged
        self.enrollment.refresh_from_db()
        assert self.enrollment.status == Enrollment.STATUS_ENROLLMENT_GENERATED
        assert self.enrollment.admission_number == 'ADM123'
        assert self.enrollment.registration_number == 'REG456'
        
        # 5. Verify a separate PaymentLedger record is captured
        initial_ledger.refresh_from_db()
        assert initial_ledger.amount_paid == Decimal('8000.00') # Unchanged
        
        repay_ledger = PaymentLedger.all_objects.get(transaction_ref='repay_ref_001')
        assert repay_ledger.amount_paid == Decimal('7000.00')
        assert repay_ledger.status == PaymentLedger.STATUS_CAPTURED
        assert repay_ledger.enrollment == self.enrollment

        # 6. Verify payout splits calculations are correct
        payouts = UniversityPayoutLedger.all_objects.filter(transaction__gateway_reference='repay_ref_001')
        assert payouts.count() == 1
        assert payouts.first().payable_to_univ == Decimal('3500.00') # 50% university share of 7000

        # 7. Verify duplicate webhook call is idempotent and does not recreate ledgers
        resp = anon_client.post(
            '/api/v1/webhooks/payment/',
            json.dumps({
                'invoice_id': invoice_id,
                'status': 'success',
                'gateway_reference': 'repay_ref_001'
            }),
            content_type='application/json'
        )
        # Duplicate gateway references trigger a database integrity rollback/error or ignored if processed
        assert resp.status_code in (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST)
        assert PaymentLedger.all_objects.filter(transaction_ref='repay_ref_001').count() == 1
        assert UniversityPayoutLedger.all_objects.filter(transaction__gateway_reference='repay_ref_001').count() == 1

    def test_razorpay_webhook_flow_keeps_status_for_repayment(self):
        """Verify integrations razorpay_webhook behaves identically for repayments."""
        # Setup initial captured payment
        PaymentLedger.all_objects.create(
            enrollment=self.enrollment,
            sub_center=self.center_a,
            amount_paid=Decimal('8000.00'),
            transaction_ref='initial_rp_ref',
            status=PaymentLedger.STATUS_CAPTURED
        )
        
        Enrollment.all_objects.filter(id=self.enrollment.id).update(
            status=Enrollment.STATUS_ENROLLMENT_GENERATED,
            admission_number='ADM123',
            registration_number='REG456'
        )
        self.enrollment.refresh_from_db()
        
        # Simulate Razorpay webhook payment capture event for repayment
        anon_client = Client()
        webhook_payload = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'repay_rp_ref_002',
                        'amount': 700000,  # paise
                        'notes': {'enrollment_id': str(self.enrollment.id)},
                    }
                }
            }
        }
        resp = anon_client.post(
            '/webhooks/razorpay/payments/',
            data=json.dumps(webhook_payload),
            content_type='application/json'
        )
        assert resp.status_code == 200
        
        # Verify enrollment status remains Enrollment Generated
        self.enrollment.refresh_from_db()
        assert self.enrollment.status == Enrollment.STATUS_ENROLLMENT_GENERATED
        assert self.enrollment.admission_number == 'ADM123'
        assert self.enrollment.registration_number == 'REG456'
        
        # Verify PaymentLedger created
        ledger = PaymentLedger.all_objects.get(transaction_ref='repay_rp_ref_002')
        assert ledger.amount_paid == Decimal('7000.00')

    def test_multiple_enrollments_isolation(self):
        """Verify that payment history on Enrollment A does not classify Enrollment B's first payment as repayment."""
        # Create second enrollment for student on different course
        course_b = CourseFactory(university=self.uni)
        FeeStructureFactory(course=course_b, fee_type=FeeStructure.FEE_TUITION, amount=Decimal('5000.00'), is_active=True)
        enrollment_b = Enrollment.objects.create(
            student=self.student,
            course=course_b,
            session=self.session,
            status=Enrollment.STATUS_APPLIED,
            sub_center=self.center_a
        )

        # enrollment (Enrollment A) is paid
        PaymentLedger.all_objects.create(
            enrollment=self.enrollment,
            sub_center=self.center_a,
            amount_paid=Decimal('8000.00'),
            transaction_ref='enrollment_a_pay',
            status=PaymentLedger.STATUS_CAPTURED
        )

        # Enrollment B's first payment should evaluate is_repayment to False
        # Create an invoice for Enrollment B (initial payment)
        invoice_b = Invoice.objects.create(
            sub_center=self.center_a,
            gross_amount=Decimal('5000.00'),
            status=Invoice.STATUS_UNPAID
        )
        InvoiceLineItem.objects.create(
            invoice=invoice_b,
            student=self.student,
            course=course_b,
            course_fee=Decimal('5000.00'),
            university_share=Decimal('2500.00'),
            rimit_commission=Decimal('2500.00')
        )

        # Process payment for Enrollment B's initial invoice
        anon_client = Client()
        resp = anon_client.post(
            '/api/v1/webhooks/payment/',
            json.dumps({
                'invoice_id': str(invoice_b.id),
                'status': 'success',
                'gateway_reference': 'enrollment_b_pay_ref'
            }),
            content_type='application/json'
        )
        assert resp.status_code == status.HTTP_200_OK

        # Verify no PaymentLedger is created by PaymentWebhookView (because it is initial, not repayment)
        ledgers = PaymentLedger.all_objects.filter(transaction_ref='enrollment_b_pay_ref')
        assert ledgers.count() == 0

    def test_exact_enrollment_stored_on_initial_invoice_line_item(self):
        """Verify that initial checkout stores the exact Enrollment directly on InvoiceLineItem."""
        client = self.counselor_client(sub_center=self.center_a)
        # Update student lead status to pending and enrollment status to Fee Pending to allow initial checkout
        Student.objects.filter(id=self.student.id).update(lead_status=Student.LEAD_STATUS_PENDING)
        Enrollment.all_objects.filter(id=self.enrollment.id).update(status=Enrollment.STATUS_FEE_PENDING)
        self.student.refresh_from_db()
        self.enrollment.refresh_from_db()

        resp = client.post(
            '/api/v1/checkout/batch/',
            json.dumps({'student_ids': [str(self.student.id)]}),
            content_type='application/json'
        )
        assert resp.status_code == status.HTTP_200_OK
        invoice_id = resp.data['invoice_id']
        line_item = InvoiceLineItem.objects.get(invoice_id=invoice_id)
        assert line_item.enrollment == self.enrollment

    def test_exact_enrollment_stored_on_repayment_invoice_line_item(self):
        """Verify that repayment checkout stores the exact Enrollment directly on InvoiceLineItem."""
        Enrollment.all_objects.filter(id=self.enrollment.id).update(status=Enrollment.STATUS_ENROLLMENT_GENERATED)
        self.enrollment.refresh_from_db()
        client = self.counselor_client(sub_center=self.center_a)

        resp = client.post(f'/api/v1/enrollments/{self.enrollment.id}/repayment_checkout')
        assert resp.status_code == status.HTTP_200_OK
        invoice_id = resp.data['invoice_id']
        line_item = InvoiceLineItem.objects.get(invoice_id=invoice_id)
        assert line_item.enrollment == self.enrollment

    def test_missing_exact_enrollment_fails_safely(self):
        """Verify that initial checkout fails safely if no exact matching Enrollment is found."""
        # Setup student with no matching Enrollment record (delete the enrollment)
        self.enrollment.delete()
        client = self.counselor_client(sub_center=self.center_a)
        Student.objects.filter(id=self.student.id).update(lead_status=Student.LEAD_STATUS_PENDING)
        self.student.refresh_from_db()

        resp = client.post(
            '/api/v1/checkout/batch/',
            json.dumps({'student_ids': [str(self.student.id)]}),
            content_type='application/json'
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Enrollment not found' in resp.data['error']
        # Confirm no orphaned invoice is created
        assert Invoice.objects.filter(sub_center=self.center_a).count() == 0

    def test_legacy_enrollment_null_fallback(self):
        """Verify that legacy transactions with enrollment=NULL do not guess or crash, treating as non-repayment."""
        invoice = Invoice.objects.create(
            sub_center=self.center_a,
            gross_amount=Decimal('8000.00'),
            status=Invoice.STATUS_UNPAID
        )
        # Create line item with enrollment=None
        InvoiceLineItem.objects.create(
            invoice=invoice,
            student=self.student,
            course=self.course,
            enrollment=None,
            course_fee=Decimal('8000.00'),
            university_share=Decimal('4000.00'),
            rimit_commission=Decimal('4000.00')
        )

        anon_client = Client()
        resp = anon_client.post(
            '/api/v1/webhooks/payment/',
            json.dumps({
                'invoice_id': str(invoice.id),
                'status': 'success',
                'gateway_reference': 'legacy_ref_099'
            }),
            content_type='application/json'
        )
        assert resp.status_code == status.HTTP_200_OK

        # Legacy transaction transitions student lead status to Enrolled
        self.student.refresh_from_db()
        assert self.student.lead_status == Student.LEAD_STATUS_ENROLLED

        # No PaymentLedger repayment record should be created since it's legacy initial payment (repayment=False)
        assert PaymentLedger.all_objects.filter(transaction_ref='legacy_ref_099').count() == 0


