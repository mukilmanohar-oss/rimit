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
    """User management — Super Admin & Sub-Center Admin."""
    queryset = SystemUser.objects.select_related('user', 'sub_center').order_by('created_at')
    resource_name = 'system_user'
    permission_classes = [ResourcePermission]
    filterset_fields = ['sub_center', 'role']
    search_fields = ['email', 'phone', 'user__username']
    ordering_fields = ['created_at', 'role']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()

        try:
            su = SystemUser.objects.get(user=user)
            if su.role == SystemUser.ROLE_SUPER_ADMIN:
                return qs
            elif su.role == SystemUser.ROLE_SUBCENTER:
                if su.sub_center:
                    return qs.filter(sub_center=su.sub_center).exclude(role=SystemUser.ROLE_SUPER_ADMIN)
                return qs.none()
        except SystemUser.DoesNotExist:
            if user.is_superuser:
                return qs
        return qs.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return SystemUserCreateSerializer
        return SystemUserSerializer

    def perform_create(self, serializer):
        user = self.request.user
        try:
            su = SystemUser.objects.get(user=user)
            if su.role == SystemUser.ROLE_SUBCENTER:
                if not su.sub_center:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Sub-Center Admins must have an assigned Sub-Center to create users.")
                serializer.validated_data['sub_center'] = su.sub_center
                if serializer.validated_data.get('role') != SystemUser.ROLE_SUBCENTER:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Sub-Center Admins can only create other Sub-Center Admin users.")
        except SystemUser.DoesNotExist:
            pass
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        try:
            su = SystemUser.objects.get(user=user)
            if su.role == SystemUser.ROLE_SUBCENTER:
                # Sub-Center Admin can only update users for their own sub-center
                serializer.validated_data['sub_center'] = su.sub_center
                if serializer.validated_data.get('role') in (SystemUser.ROLE_SUPER_ADMIN,):
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Cannot set role to Super Admin.")
        except SystemUser.DoesNotExist:
            pass
        serializer.save()



class SubCenterUniversityMappingViewSet(viewsets.ModelViewSet):
    """Allow-list of universities per sub-center (Super Admin only)."""
    queryset = SubCenterUniversityMapping.objects.select_related('sub_center', 'university')
    serializer_class = SubCenterUniversityMappingSerializer
    resource_name = 'sc_uni_mapping'
    permission_classes = [ResourcePermission]
    filterset_fields = ['sub_center', 'university']
    search_fields = ['sub_center__center_code', 'sub_center__name', 'university__name']
    ordering_fields = ['created_at']
