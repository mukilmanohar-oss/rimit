"""Finance viewsets and reporting endpoints."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from apps.common.permissions import IsFinanceOrAbove
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
    permission_classes = [IsFinanceOrAbove]
    filterset_fields = ['status', 'enrollment', 'sub_center', 'gateway']
    search_fields = ['transaction_ref', 'enrollment__student__full_name']
    ordering_fields = ['created_at', 'amount_paid', 'status']

    def get_queryset(self):
        return PaymentLedger.objects.select_related('enrollment', 'enrollment__student')

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

    @action(detail=False, methods=['get'])
    def by_sub_center(self, request):
        """Breakdown of collections by sub-center."""
        from apps.common.permissions import _user_role
        qs = self.get_queryset().filter(status='captured')
        if _user_role(request) not in ('super_admin', 'academic_head'):
            return Response({'detail': 'Cross-center view not allowed'}, status=403)

        rows = qs.values('sub_center__center_code', 'sub_center__name').annotate(
            total=Sum('amount_paid'),
            count=Count('id'),
        ).order_by('-total')
        return Response(list(rows))
