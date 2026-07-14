"""ViewSets for rules app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.common.permissions import IsSuperAdmin, IsSuperAdminOrReadOnly, IsCounselorOrAbove
from apps.common.rbac import ResourcePermission
from apps.rules.models import IntakeSession, RulesConfiguration
from apps.rules.serializers import (
    IntakeSessionSerializer, RulesConfigurationSerializer, EnrollmentValidationSerializer,
)


class IntakeSessionViewSet(viewsets.ModelViewSet):
    queryset = IntakeSession.objects.all()
    serializer_class = IntakeSessionSerializer
    resource_name = 'intake_session'
    permission_classes = [ResourcePermission]
    filterset_fields = ['is_active']
    ordering_fields = ['start_date', 'session_name']
    search_fields = ['session_name']


class RulesConfigurationViewSet(viewsets.ModelViewSet):
    """Session Enforcement Matrix rules — Super Admin only."""
    queryset = RulesConfiguration.objects.all()
    serializer_class = RulesConfigurationSerializer
    resource_name = 'rules_config'
    permission_classes = [ResourcePermission]
    filterset_fields = ['is_active']
    ordering_fields = ['priority', 'rule_name']
    search_fields = ['rule_name', 'description']


class EnrollmentValidationView(APIView):
    """
    Pre-flight validation: check if an enrollment would pass
    the Session Enforcement Matrix before submission.
    """
    permission_classes = [IsCounselorOrAbove]

    def perform_authentication(self, request):
        super().perform_authentication(request)
        # Resolve tenant context after DRF auth (same as TenantAwareViewMixin)
        from apps.common.middleware import set_tenant_context
        set_tenant_context(request.user)

    def post(self, request):
        from apps.admissions.models import Student, Enrollment
        from apps.aggregator.models import Course
        from apps.rules.engine import validate_enrollment
        from apps.common.permissions import _user_role

        serializer = EnrollmentValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            student = Student.objects.get(id=data['student'])
            course = Course.objects.get(id=data['course'])
            session = IntakeSession.objects.get(id=data['session'])
        except (Student.DoesNotExist, Course.DoesNotExist, IntakeSession.DoesNotExist) as e:
            return Response({'detail': str(e)}, status=404)

        # Tenant boundary: non-super-admin can only validate own students
        role = _user_role(request)
        if role not in ('super_admin', 'academic_head'):
            try:
                user_sub_center = request.user.systemuser.sub_center_id
            except Exception:
                return Response({'detail': 'No tenant context'}, status=403)
            if student.sub_center_id != user_sub_center:
                return Response({'detail': 'Not your student'}, status=403)

        result = validate_enrollment(student, course, session)
        return Response({
            'valid': result.valid,
            'reason': result.reason,
            'matched_rule': result.matched_rule_name,
            'suggested_session_id': str(result.suggested_session_id) if result.suggested_session_id else None,
        })
