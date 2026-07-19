"""ViewSets for aggregator app."""
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.rbac import ResourcePermission
from apps.common.views import TenantAwareViewMixin
from apps.aggregator.models import University, Course, FeeStructure, UniversityDocVault
from apps.aggregator.serializers import (
    UniversitySerializer, UniversityDetailSerializer,
    CourseSerializer, CourseListSerializer,
    FeeStructureSerializer, UniversityDocVaultSerializer,
)


class UniversityViewSet(TenantAwareViewMixin, viewsets.ModelViewSet):
    """
    University directory.

    - super_admin: full CRUD
    - academic_head: read all
    - any authenticated user: read all
    """
    queryset = University.objects.prefetch_related('documents', 'courses', 'courses__fees')
    permission_classes = [ResourcePermission]
    resource_name = 'university'
    filterset_fields = ['state', 'is_active']
    search_fields = ['name', 'state', 'accreditation', 'description']
    ordering_fields = ['name', 'state', 'created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UniversityDetailSerializer
        return UniversitySerializer

    def get_queryset(self):
        """Return universities visible to the requester.

        Visibility rules:
          - super_admin: all (including inactive)
          - academic_head: active universities
          - counselor/finance: ONLY universities explicitly mapped to their sub-center
        """
        from apps.common.permissions import _user_role
        role = _user_role(self.request)

        qs = super().get_queryset()

        if role != 'super_admin':
            qs = qs.filter(is_active=True)

        if role in ('counselor', 'finance'):
            from apps.common.middleware import _current_tenant_id
            from apps.partners.models import SubCenterUniversityMapping
            tenant_id = _current_tenant_id()
            if tenant_id is None:
                return qs.none()
            allowed_unis = SubCenterUniversityMapping.objects.filter(
                sub_center_id=tenant_id
            ).values_list('university_id', flat=True)
            qs = qs.filter(id__in=allowed_unis)

        return qs


class CourseViewSet(TenantAwareViewMixin, viewsets.ModelViewSet):
    """
    Course & Fee Search Engine.

    - super_admin: full CRUD
    - any authenticated user: read all (with multi-attribute filter)
    """
    queryset = Course.objects.select_related('university').prefetch_related('fees')
    permission_classes = [ResourcePermission]
    resource_name = 'course'
    filterset_fields = ['university', 'stream', 'is_active']
    search_fields = ['name', 'stream', 'eligibility_text', 'university__name']
    ordering_fields = ['name', 'stream', 'duration_months', 'created_at']
    ordering = ('name', 'id')

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseSerializer

    def get_queryset(self):
        from apps.common.permissions import _user_role
        from django.db.models import Q, Sum
        role = _user_role(self.request)
        qs = super().get_queryset()
        if role != 'super_admin':
            qs = qs.filter(is_active=True)

        # Sub-center visibility allow-list
        if role in ('counselor', 'finance'):
            from apps.common.middleware import _current_tenant_id
            from apps.partners.models import SubCenterUniversityMapping
            tenant_id = _current_tenant_id()
            if tenant_id is None:
                return qs.none()
            allowed_unis = SubCenterUniversityMapping.objects.filter(
                sub_center_id=tenant_id
            ).values_list('university_id', flat=True)
            qs = qs.filter(university_id__in=allowed_unis)

        # Multi-attribute search (RFP: stream, eligibility, duration, budget)
        params = self.request.query_params
        budget_max = params.get('budget_max')
        if budget_max:
            # Filter courses whose total fee <= budget_max
            qs = qs.annotate(
                total_fee=Sum('fees__amount', filter=Q(fees__is_active=True))
            ).filter(total_fee__lte=budget_max)
        return qs

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def commission(self, request, pk=None):
        """Get commission breakdown for this course."""
        from decimal import Decimal
        from apps.common.middleware import _current_tenant_id
        from apps.finance.models import SubCenterCommission
        from apps.partners.models import SubCenter
        from apps.finance.net_remittance import calculate_net_remittance
        from apps.aggregator.serializers import CourseCommissionBreakdownSerializer

        course = self.get_object()
        total_fee = sum(f.amount for f in course.fees.filter(is_active=True))
        total_fee_d = Decimal(str(total_fee))

        uni_pct = course.university_share_percent
        if uni_pct is None:
            uni_pct = course.university.default_university_share_percent

        tenant_id = _current_tenant_id()
        sc_comm_pct = Decimal('0.00')

        if tenant_id:
            sc_comm = SubCenterCommission.objects.filter(sub_center_id=tenant_id, course=course).first()
            if sc_comm:
                sc_comm_pct = sc_comm.commission_percent
            else:
                # Fallback to subcenter default
                sc = SubCenter.objects.filter(id=tenant_id).first()
                if sc:
                    sc_comm_pct = sc.commission_percent

        breakdown = calculate_net_remittance(
            total_fee=total_fee_d,
            university_share_percent=uni_pct,
            sub_center_commission_percent=sc_comm_pct,
        )

        data = {
            'course_id': course.id,
            'course_name': course.name,
            'university_name': course.university.name,
            'total_course_fee': breakdown.total_fee,
            'university_share': breakdown.university_share,
            'university_share_percent': breakdown.university_share_percent,
            'default_university_share_percent': course.university.default_university_share_percent,
            'course_specific_university_share_percent': course.university_share_percent,
            'gross_commission_pool': breakdown.gross_pool,
            'sub_center_commission': breakdown.sub_center_commission,
            'sub_center_commission_percent': breakdown.sub_center_commission_percent,
            'rimit_commission': breakdown.rimit_commission,
            'amount_payable_to_university': breakdown.university_share,
            'net_payable': breakdown.net_payable,
        }

        serializer = CourseCommissionBreakdownSerializer(data)
        return Response(serializer.data)



class FeeStructureViewSet(TenantAwareViewMixin, viewsets.ModelViewSet):
    queryset = FeeStructure.objects.select_related('course')
    serializer_class = FeeStructureSerializer
    permission_classes = [ResourcePermission]
    resource_name = 'fee_structure'
    filterset_fields = ['course', 'fee_type', 'is_active']
    ordering_fields = ['fee_type', 'amount', 'created_at']

    def get_queryset(self):
        """Fees must not leak catalog details outside allowed universities."""
        from apps.common.permissions import _user_role
        role = _user_role(self.request)
        qs = super().get_queryset()
        if role in ('counselor', 'finance'):
            from apps.common.middleware import _current_tenant_id
            from apps.partners.models import SubCenterUniversityMapping
            tenant_id = _current_tenant_id()
            if tenant_id is None:
                return qs.none()
            allowed_unis = SubCenterUniversityMapping.objects.filter(
                sub_center_id=tenant_id
            ).values_list('university_id', flat=True)
            qs = qs.filter(course__university_id__in=allowed_unis)
        return qs


class UniversityDocVaultViewSet(TenantAwareViewMixin, viewsets.ModelViewSet):
    """
    Digital Prospectus Library.

    - super_admin: full CRUD
    - any authenticated user: read, download via presigned URL endpoint
    """
    queryset = UniversityDocVault.objects.select_related('university')
    serializer_class = UniversityDocVaultSerializer
    permission_classes = [ResourcePermission]
    resource_name = 'university_doc'
    filterset_fields = ['university', 'doc_type', 'is_public', 'course']
    search_fields = ['title', 'university__name']
    ordering_fields = ['title', 'created_at']

    def perform_create(self, serializer):
        from apps.common.utils_storage import handle_file_upload
        file_obj = self.request.FILES.get('file')
        if file_obj:
            uri = handle_file_upload(file_obj, directory=f"university/{self.request.data.get('university')}/")
            serializer.save(
                s3_object_uri=uri,
                file_size_bytes=file_obj.size,
                mime_type=file_obj.content_type or 'application/octet-stream'
            )
        else:
            serializer.save()

    def perform_update(self, serializer):
        from apps.common.utils_storage import handle_file_upload
        file_obj = self.request.FILES.get('file')
        if file_obj:
            doc = self.get_object()
            uri = handle_file_upload(file_obj, directory=f"university/{doc.university_id}/")
            serializer.save(
                s3_object_uri=uri,
                file_size_bytes=file_obj.size,
                mime_type=file_obj.content_type or 'application/octet-stream'
            )
        else:
            serializer.save()

    def get_queryset(self):
        """Prospectus library must respect the same visibility allow-list."""
        from apps.common.permissions import _user_role
        role = _user_role(self.request)
        qs = super().get_queryset()
        if role in ('counselor', 'finance'):
            from apps.common.middleware import _current_tenant_id
            from apps.partners.models import SubCenterUniversityMapping
            tenant_id = _current_tenant_id()
            if tenant_id is None:
                return qs.none()
            allowed_unis = SubCenterUniversityMapping.objects.filter(
                sub_center_id=tenant_id
            ).values_list('university_id', flat=True)
            qs = qs.filter(university_id__in=allowed_unis)
        return qs

    @extend_schema(description="Generate presigned download URL (15-min TTL)")
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """Return presigned URL for document download (15-min TTL)."""
        doc = self.get_object()
        from apps.common.utils_storage import get_presigned_url
        presigned_url = get_presigned_url(doc.s3_object_uri, expires_in=900)
        
        return Response({
            'url': presigned_url,
            'ttl_seconds': 900,
            'expires_in': '15 minutes',
            'filename': doc.title,
        })
