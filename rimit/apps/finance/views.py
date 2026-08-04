"""Finance viewsets and reporting endpoints."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from apps.common.permissions import IsFinanceOrAbove
from apps.common.rbac import ResourcePermission
from apps.common.views import TenantAwareViewMixin
from apps.finance.models import PaymentLedger
from apps.finance.serializers import PaymentLedgerSerializer


class PaymentLedgerViewSet(TenantAwareViewMixin, viewsets.ReadOnlyModelViewSet):
    """
    Payment ledger - read-only via API.
    Writes happen only via Razorpay webhook (server-to-server).
    """
    queryset = PaymentLedger.all_objects.select_related('enrollment', 'enrollment__student')
    serializer_class = PaymentLedgerSerializer
    resource_name = 'payment'
    permission_classes = [ResourcePermission]
    filterset_fields = ['status', 'enrollment', 'sub_center', 'gateway']
    search_fields = ['transaction_ref', 'enrollment__student__full_name']
    ordering_fields = ['created_at', 'amount_paid', 'status']

    def get_queryset(self):
        return PaymentLedger.objects.select_related('enrollment', 'enrollment__student')

    from apps.common.permissions import IsCounselorOrAbove
    @action(detail=False, methods=['POST'], permission_classes=[IsCounselorOrAbove])
    def mock_payment(self, request):
        """Mock a successful payment capture (for dev UI testing)."""
        from apps.admissions.models import Enrollment
        from decimal import Decimal
        import uuid
        
        enrollment_id = request.data.get("enrollment_id")
        amount = request.data.get("amount")
        
        if not enrollment_id or not amount:
            return Response({"error": "enrollment_id and amount required"}, status=400)
            
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return Response({"error": "Enrollment not found"}, status=404)
            
        # Create a captured payment ledger
        ledger = PaymentLedger.objects.create(
            enrollment=enrollment,
            sub_center=enrollment.sub_center,
            amount_paid=Decimal(amount),
            gateway="razorpay_mock",
            transaction_ref=f"pay_mock_{uuid.uuid4().hex[:10]}",
            status="captured",
            gateway_response={"mock": True}
        )
        
        return Response({"message": "Mock payment created", "ledger_id": str(ledger.id)})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Financial dashboard summary: total collected, pending, count."""
        from apps.common.permissions import _user_role
        qs = self.get_queryset()
        if _user_role(request) not in ('super_admin', 'academic_head'):
            # Filter to own tenant
            pass  # TenantManager already filters

        agg = qs.aggregate(
            total_collected=Sum('amount_paid', filter=Q(status='captured')),
            total_pending=Sum('amount_paid', filter=Q(status='pending')),
            captured_count=Count('id', filter=Q(status='captured')),
            pending_count=Count('id', filter=Q(status='pending')),
        )
        return Response(agg)

    @action(detail=False, methods=['get'], permission_classes=[ResourcePermission])
    def by_sub_center(self, request):
        """Breakdown of collections by sub-center."""
        # Note: ResourcePermission uses 'breakdown' action via the decorator 
        # so it maps perfectly to the matrix: 'breakdown': [SA, AH]
        qs = self.get_queryset().filter(status='captured')

        rows = qs.values('sub_center__center_code', 'sub_center__name').annotate(
            total=Sum('amount_paid'),
            count=Count('id'),
        ).order_by('-total')
        return Response(list(rows))

from rest_framework.views import APIView
from apps.common.views import TenantAwareViewMixin
from django.db import transaction
from django.db.models import Sum
from apps.admissions.models import Student
from apps.finance.models import Invoice, InvoiceLineItem, Transaction
from apps.common.middleware import _current_tenant_id
import uuid
from apps.common.rbac import ResourcePermission
from rest_framework.permissions import AllowAny

class BatchCheckoutView(APIView):
    resource_name = 'checkout'
    permission_classes = [ResourcePermission]

    def post(self, request):
        from apps.finance.serializers import BatchCheckoutSerializer
        payload = BatchCheckoutSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        student_ids = payload.validated_data['student_ids']

        # Resolve role & tenant directly from request.user (DRF token auth
        # has already authenticated by the time this view method runs).
        from apps.partners.models import SystemUser as SU

        role = None
        tenant_id = None
        try:
            su = SU.objects.get(user=request.user)
            role = su.role
            tenant_id = str(su.sub_center_id) if su.sub_center_id else None
        except SU.DoesNotExist:
            if request.user.is_superuser:
                role = 'super_admin'

        privileged = role in ('super_admin', 'academic_head')

        if privileged:
            students = Student.all_objects.using('default').filter(
                id__in=student_ids,
                lead_status=Student.LEAD_STATUS_PENDING
            ).select_related('course', 'course__university', 'sub_center')
        else:
            if not tenant_id:
                return Response({'error': 'No sub-center associated with your account.'}, status=403)
            students = Student.all_objects.using('default').filter(
                id__in=student_ids,
                sub_center_id=tenant_id,
                lead_status=Student.LEAD_STATUS_PENDING
            ).select_related('course', 'course__university')

        if students.count() != len(student_ids):
            return Response({'error': 'Some students are invalid, belong to another center, or are not in Pending state.'}, status=400)

        # Enforce single-tenant invoice (critical for commission % and tenant scoping)
        distinct_centers = {str(s.sub_center_id) for s in students}
        if len(distinct_centers) != 1:
            return Response({'error': 'All selected students must belong to the same sub-center.'}, status=400)
        effective_tenant_id = distinct_centers.pop()

        from apps.partners.models import SubCenter
        try:
            sub_center = SubCenter.objects.get(id=effective_tenant_id)
        except SubCenter.DoesNotExist:
            return Response({'error': 'Sub-center not found.'}, status=400)

        from apps.finance.net_remittance import calculate_net_remittance, NetRemittanceError
        from decimal import Decimal

        # Pre-validate: every selected student must have a course
        missing_course = [str(s.id) for s in students if not s.course_id]
        if missing_course:
            return Response({'error': f'Cannot checkout: students missing course assignment: {missing_course}'}, status=400)

        with transaction.atomic():
            invoice = Invoice.objects.create(gross_amount=0, sub_center_id=effective_tenant_id)
            total_gross = Decimal('0.00')
            total_sc_deducted = Decimal('0.00')
            total_net = Decimal('0.00')
            line_items_out = []

            for student in students:
                course = student.course

                fee = course.fees.filter(is_active=True).aggregate(t=Sum('amount'))['t'] or 0
                fee = Decimal(str(fee))

                uni_pct = course.university_share_percent
                if uni_pct is None:
                    uni_pct = course.university.default_university_share_percent

                # Fetch specific sub-center commission for this course
                from apps.finance.models import SubCenterCommission
                sc_comm = SubCenterCommission.objects.filter(sub_center_id=effective_tenant_id, course=course).first()
                sc_comm_pct = sc_comm.commission_percent if sc_comm else Decimal('0.00')

                try:
                    breakdown = calculate_net_remittance(
                        total_fee=fee,
                        university_share_percent=uni_pct,
                        sub_center_commission_percent=sc_comm_pct,
                    )
                except NetRemittanceError as e:
                    return Response({'error': str(e)}, status=400)

                total_gross += fee
                total_sc_deducted += breakdown.sub_center_commission
                total_net += breakdown.net_payable

                from apps.admissions.models import Enrollment
                try:
                    exact_enrollment = Enrollment.all_objects.get(
                        student=student,
                        course=student.course,
                        session=student.session
                    )
                except Enrollment.DoesNotExist:
                    return Response({'error': f'Enrollment not found for student {student.full_name}'}, status=400)

                li = InvoiceLineItem.objects.create(
                    invoice=invoice,
                    student=student,
                    course=course,
                    enrollment=exact_enrollment,
                    course_fee=breakdown.total_fee,
                    university_share_percent=breakdown.university_share_percent,
                    university_share=breakdown.university_share,
                    gross_pool=breakdown.gross_pool,
                    sub_center_commission_percent=breakdown.sub_center_commission_percent,
                    sub_center_commission=breakdown.sub_center_commission,
                    rimit_commission=breakdown.rimit_commission,
                    net_payable=breakdown.net_payable,
                )

                line_items_out.append({
                    'student_id': str(student.id),
                    'student_name': student.full_name,
                    'course_id': str(course.id),
                    'course_name': course.name,
                    'university_id': str(course.university_id),
                    'university_name': course.university.name,
                    'total_fee': str(breakdown.total_fee),
                    'university_share': str(breakdown.university_share),
                    'sub_center_commission': str(breakdown.sub_center_commission),
                    'rimit_commission': str(breakdown.rimit_commission),
                    'net_payable': str(breakdown.net_payable),
                    'university_share_percent': str(breakdown.university_share_percent),
                    'sub_center_commission_percent': str(breakdown.sub_center_commission_percent),
                })

            invoice.gross_amount = total_gross
            invoice.sub_center_commission_deducted = total_sc_deducted
            invoice.net_payable_collected = total_net
            invoice.save(update_fields=['gross_amount', 'sub_center_commission_deducted', 'net_payable_collected'])

            gateway_token = uuid.uuid4().hex

        from apps.common.payment_helpers import get_gateway_checkout_url
        checkout_url = get_gateway_checkout_url(request, gateway_token, str(invoice.id))

        return Response({
            'message': 'Batch checkout initiated',
            'invoice_id': str(invoice.id),
            'gross_amount': str(total_gross),
            'sub_center_commission_deducted': str(total_sc_deducted),
            'net_payable_collected': str(total_net),
            'line_items': line_items_out,
            'gateway_redirect_url': checkout_url
        })



class PaymentWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        # MOCK HMAC CHECK
        # In production, we'd verify Razorpay signature here.
        # if not verify_hmac(request.body, request.headers.get('x-razorpay-signature')):
        #     return Response({'error': 'Invalid signature'}, status=400)

        invoice_id = request.data.get('invoice_id')
        status = request.data.get('status') # 'success' or 'failed'
        gateway_ref = request.data.get('gateway_reference')
        
        if not all([invoice_id, status, gateway_ref]):
            return Response({'error': 'Invalid payload'}, status=400)
            
        try:
            invoice = Invoice.all_objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=404)

        from django.db import IntegrityError
        try:
            with transaction.atomic():
                txn = Transaction.objects.create(
                    invoice=invoice,
                    gateway_reference=gateway_ref,
                    amount_paid=invoice.net_payable_collected,
                    status=Transaction.STATUS_SUCCESS if status == 'success' else Transaction.STATUS_FAILED
                )

                if status == 'success':
                    invoice.status = Invoice.STATUS_PAID
                    invoice.save(update_fields=['status'])

                    # Check if this invoice is a repayment invoice
                    line_item = invoice.line_items.first()
                    if line_item and line_item.enrollment:
                        from apps.finance.models import PaymentLedger
                        enrollment = line_item.enrollment
                        is_repayment = PaymentLedger.all_objects.filter(
                            enrollment=enrollment,
                            status=PaymentLedger.STATUS_CAPTURED
                        ).exclude(transaction_ref=gateway_ref).exists()

                        if is_repayment:
                            PaymentLedger.all_objects.get_or_create(
                                transaction_ref=gateway_ref,
                                defaults={
                                    'enrollment': enrollment,
                                    'sub_center': enrollment.sub_center,
                                    'amount_paid': invoice.net_payable_collected,
                                    'status': PaymentLedger.STATUS_CAPTURED,
                                    'gateway_response': {"invoice_id": invoice_id}
                                }
                            )

                    # Run settlement SYNCHRONOUSLY for mock/dev
                    try:
                        from apps.finance.tasks import process_ledger_settlement
                        process_ledger_settlement(str(txn.id))
                    except ImportError:
                        pass
                else:
                    invoice.status = Invoice.STATUS_FAILED
                    invoice.save(update_fields=['status'])
        except IntegrityError:
            exists = Transaction.objects.filter(gateway_reference=gateway_ref, status=Transaction.STATUS_SUCCESS).exists()
            if exists:
                return Response({'status': 'Webhook processed'}, status=200)
            return Response({'error': 'Duplicate transaction reference'}, status=400)

        return Response({'status': 'Webhook processed'}, status=200)


def mock_checkout_view(request, token):
    from django.http import HttpResponse, HttpResponseForbidden
    from django.conf import settings
    from apps.finance.models import Invoice

    if not getattr(settings, 'MOCK_GATEWAY_ENABLED', False):
        return HttpResponseForbidden("Mock gateway is disabled.")

    invoice_id = request.GET.get('invoice')
    if not invoice_id:
        return HttpResponse("Invoice ID query param missing.", status=400)

    try:
        invoice = Invoice.all_objects.get(id=invoice_id)
    except (Invoice.DoesNotExist, ValueError):
        return HttpResponse("Invoice not found.", status=404)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Mock Payment Gateway Checkout</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #f3f4f6;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }}
            .card {{
                background-color: #ffffff;
                padding: 2.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
                max-width: 450px;
                width: 100%;
                text-align: center;
            }}
            h2 {{ color: #111827; margin-bottom: 1.5rem; }}
            .detail {{ font-size: 1.1rem; color: #4b5563; margin-bottom: 0.75rem; }}
            .amount {{ font-size: 1.8rem; font-weight: bold; color: #059669; margin: 1.5rem 0; }}
            .btn-group {{ display: flex; gap: 1rem; justify-content: center; margin-top: 2rem; }}
            button {{
                padding: 0.75rem 1.5rem;
                border-radius: 6px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                border: none;
                transition: background-color 0.2s;
                width: 50%;
            }}
            .btn-success {{ background-color: #059669; color: white; }}
            .btn-success:hover {{ background-color: #047857; }}
            .btn-fail {{ background-color: #dc2626; color: white; }}
            .btn-fail:hover {{ background-color: #b91c1c; }}
            #status-message {{ margin-top: 1.5rem; font-weight: 500; font-size: 1.05rem; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Mock Gateway Payment</h2>
            <div class="detail"><strong>Invoice ID:</strong> {invoice.id}</div>
            <div class="detail"><strong>Sub-Center:</strong> {invoice.sub_center.name}</div>
            <div class="amount">₹{invoice.net_payable_collected}</div>

            <div class="btn-group">
                <button class="btn-success" onclick="submitPayment('success')">Simulate Success</button>
                <button class="btn-fail" onclick="submitPayment('failed')">Simulate Failure</button>
            </div>

            <div id="status-message"></div>
        </div>

        <script>
            function submitPayment(status) {{
                const msgDiv = document.getElementById('status-message');
                msgDiv.style.color = '#374151';
                msgDiv.innerText = "Processing mock callback...";

                const gatewayRef = "pay_" + Math.random().toString(36).substring(2, 15);

                const urlParams = new URLSearchParams(window.location.search);
                const transformPort = urlParams.get('XTransformPort');

                let webhookUrl = '/api/v1/webhooks/payment/';
                if (transformPort) {{
                    webhookUrl += '?XTransformPort=' + transformPort;
                }}

                fetch(webhookUrl, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        invoice_id: "{invoice.id}",
                        status: status,
                        gateway_reference: gatewayRef
                    }})
                }})
                .then(response => {{
                    if (response.ok) {{
                        return response.json();
                    }}
                    return response.json().then(err => {{ throw new Error(err.error || 'Webhook failed'); }});
                }})
                .then(data => {{
                    msgDiv.style.color = status === 'success' ? '#059669' : '#dc2626';
                    msgDiv.innerText = "Payment completed: " + status.toUpperCase();
                    setTimeout(() => {{
                        alert("Mock payment completed successfully! You can close this tab now.");
                    }}, 500);
                }})
                .catch(err => {{
                    msgDiv.style.color = '#dc2626';
                    msgDiv.innerText = "Error: " + err.message;
                }});
            }}
        </script>
    </body>
    </html>
    """
    return HttpResponse(html_content)
