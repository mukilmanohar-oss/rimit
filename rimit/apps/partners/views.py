"""ViewSets for partners app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.permissions import IsSuperAdmin, IsSuperAdminOrReadOnly, IsTenantMember
from apps.partners.models import SubCenter, SystemUser
from apps.partners.serializers import (
    SubCenterSerializer, SystemUserSerializer, SystemUserCreateSerializer,
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
    permission_classes = [IsSuperAdminOrReadOnly]
    filterset_fields = ['status', 'state']
    search_fields = ['center_code', 'name', 'location']
    ordering_fields = ['center_code', 'name', 'created_at']


class SystemUserViewSet(viewsets.ModelViewSet):
    """User management — Super Admin only."""
    queryset = SystemUser.objects.all()
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['role', 'sub_center']
    search_fields = ['email', 'phone']
    ordering_fields = ['email', 'role', 'created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return SystemUserCreateSerializer
        return SystemUserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsTenantMember])
    def me(self, request):
        """Current user's profile."""
        try:
            su = SystemUser.objects.get(user=request.user)
            return Response(SystemUserSerializer(su).data)
        except SystemUser.DoesNotExist:
            return Response({'detail': 'No SystemUser profile'}, status=404)
