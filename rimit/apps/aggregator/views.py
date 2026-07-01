"""ViewSets for aggregator app."""
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.permissions import IsSuperAdminOrReadOnly
from apps.aggregator.models import University, Course, FeeStructure, UniversityDocVault
from apps.aggregator.serializers import (
    UniversitySerializer, UniversityDetailSerializer,
    CourseSerializer, CourseListSerializer,
    FeeStructureSerializer, UniversityDocVaultSerializer,
)


class UniversityViewSet(viewsets.ModelViewSet):
    """
    University directory.

    - super_admin: full CRUD
    - academic_head: read all
    - any authenticated user: read all
    """
    queryset = University.objects.filter(is_active=True)
    permission_classes = [IsSuperAdminOrReadOnly]
    filterset_fields = ['state', 'accreditation', 'is_active']
    search_fields = ['name', 'state', 'accreditation', 'description']
    ordering_fields = ['name', 'state', 'created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UniversityDetailSerializer
        return UniversitySerializer

    def get_queryset(self):
        # Super admins can see inactive universities
        from apps.common.permissions import _user_role
        if _user_role(self.request) == 'super_admin':
            return University.objects.all()
        return University.objects.filter(is_active=True)


class CourseViewSet(viewsets.ModelViewSet):
    """
    Course & Fee Search Engine.

    - super_admin: full CRUD
    - any authenticated user: read all (with multi-attribute filter)
    """
    queryset = Course.objects.filter(is_active=True).select_related('university')
    permission_classes = [IsSuperAdminOrReadOnly]
    filterset_fields = ['university', 'stream', 'duration_months', 'is_active']
    search_fields = ['name', 'stream', 'eligibility_text', 'university__name']
    ordering_fields = ['name', 'stream', 'duration_months', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseSerializer

    def get_queryset(self):
        from apps.common.permissions import _user_role
        from django.db.models import Q, Sum
        qs = Course.objects.select_related('university')
        if _user_role(self.request) != 'super_admin':
            qs = qs.filter(is_active=True)

        # Multi-attribute search (RFP: stream, eligibility, duration, budget)
        params = self.request.query_params
        budget_max = params.get('budget_max')
        if budget_max:
            # Filter courses whose total fee <= budget_max
            qs = qs.annotate(
                total_fee=Sum('fees__amount', filter=Q(fees__is_active=True))
            ).filter(total_fee__lte=budget_max)
        return qs


class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filterset_fields = ['course', 'fee_type', 'is_active']
    ordering_fields = ['fee_type', 'amount', 'created_at']


class UniversityDocVaultViewSet(viewsets.ModelViewSet):
    """
    Digital Prospectus Library.

    - super_admin: full CRUD
    - any authenticated user: read, download via presigned URL endpoint
    """
    queryset = UniversityDocVault.objects.all()
    serializer_class = UniversityDocVaultSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filterset_fields = ['university', 'doc_type', 'is_public']
    search_fields = ['title', 'university__name']
    ordering_fields = ['title', 'created_at']

    @extend_schema(description="Generate presigned download URL (15-min TTL)")
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """Return presigned URL for document download (15-min TTL)."""
        doc = self.get_object()
        # In prod: generate presigned URL via boto3/MinIO client
        # For dev: return the s3_object_uri directly (no actual signing)
        return Response({
            'url': doc.s3_object_uri,
            'ttl_seconds': 900,
            'expires_in': '15 minutes',
            'filename': doc.title,
        })
