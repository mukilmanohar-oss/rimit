"""ViewSets for partners app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.permissions import IsSuperAdmin, IsSuperAdminOrReadOnly, IsTenantMember
from apps.common.rbac import ResourcePermission
from apps.partners.models import SubCenter, SystemUser, SubCenterUniversityMapping
from apps.partners.serializers import (
    SubCenterSerializer, SystemUserSerializer, SystemUserCreateSerializer,
    SubCenterUniversityMappingSerializer,
)


class SubCenterViewSet(viewsets.ModelViewSet):
    """
    Sub-Center management.

    - super_admin: full CRUD on all sub-centers
    - academic_head: read all
    - counselor / finance: read own center only (TenantManager handles scoping)
    """
    queryset = SubCenter.objects.all()
    serializer_class = SubCenterSerializer
    resource_name = 'sub_center'
    permission_classes = [ResourcePermission]
    filterset_fields = ['status', 'state']
    search_fields = ['center_code', 'name', 'location']
    ordering_fields = ['center_code', 'name', 'created_at']


class SystemUserViewSet(viewsets.ModelViewSet):
    """User management — Super Admin only."""
    queryset = SystemUser.objects.select_related('user', 'sub_center')
    resource_name = 'system_user'
    permission_classes = [ResourcePermission]
    filterset_fields = ['sub_center', 'role']
    search_fields = ['email', 'phone', 'user__username']
    ordering_fields = ['created_at', 'role']

    def get_serializer_class(self):
        if self.action == 'create':
            return SystemUserCreateSerializer
        return SystemUserSerializer


class SubCenterUniversityMappingViewSet(viewsets.ModelViewSet):
    """Allow-list of universities per sub-center (Super Admin only)."""
    queryset = SubCenterUniversityMapping.objects.select_related('sub_center', 'university')
    serializer_class = SubCenterUniversityMappingSerializer
    resource_name = 'sc_uni_mapping'
    permission_classes = [ResourcePermission]
    filterset_fields = ['sub_center', 'university']
    search_fields = ['sub_center__center_code', 'sub_center__name', 'university__name']
    ordering_fields = ['created_at']
