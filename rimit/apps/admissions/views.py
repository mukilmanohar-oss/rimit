"""ViewSets for admissions app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.permissions import IsCounselorOrAbove, IsTenantMember, IsFinanceOrAbove, IsSuperAdminOrReadOnly
from apps.common.views import TenantAwareViewMixin
from apps.admissions.models import Student, StudentAcademicHistory, StudentDoc, Enrollment
from apps.admissions.serializers import (
    StudentSerializer, StudentListSerializer,
    StudentAcademicHistorySerializer, StudentDocSerializer,
    EnrollmentSerializer, EnrollmentStatusTransitionSerializer,
)


class StudentViewSet(TenantAwareViewMixin, viewsets.ModelViewSet):
    """
    Student registration and management.

    - super_admin: see all (TenantManager bypassed)
    - academic_head: see all (read-only)
    - counselor: see/create/update own sub-center's students
    - finance: read own sub-center's students (for payment context)
    """
    queryset = Student.all_objects.select_related('sub_center')
    permission_classes = [IsTenantMember]
    filterset_fields = ['sub_center', 'is_active', 'gender']
    search_fields = ['full_name', 'primary_phone', 'email', 'parent_name']
    ordering_fields = ['full_name', 'created_at', 'dob']

    def get_permissions(self):
        """Write operations require counselor or above; reads allow finance."""
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'academic_histories'):
            return [IsCounselorOrAbove()]
        return [IsTenantMember()]

    def get_queryset(self):
        return Student.objects.select_related('sub_center')

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        return StudentSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsCounselorOrAbove])
    def academic_histories(self, request, pk=None):
        """Add an academic history entry to a student."""
        student = self.get_object()
        serializer = StudentAcademicHistorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(student=student)
        return Response(serializer.data, status=201)


class StudentAcademicHistoryViewSet(viewsets.ModelViewSet):
    queryset = StudentAcademicHistory.objects.select_related('student')
    serializer_class = StudentAcademicHistorySerializer
    permission_classes = [IsCounselorOrAbove]
    filterset_fields = ['student', 'qualification']


class StudentDocViewSet(TenantAwareViewMixin, viewsets.ModelViewSet):
    """
    Document upload vault for students.

    Accepts multipart uploads (10-100MB per RFP).
    In prod, file is spooled to disk via TemporaryFileUploadHandler
    then uploaded to MinIO by a Celery task.
    """
    queryset = StudentDoc.objects.select_related('student', 'academic_history', 'verified_by')
    serializer_class = StudentDocSerializer
    permission_classes = [IsCounselorOrAbove]
    filterset_fields = ['student', 'doc_category', 'status']
    search_fields = ['title', 'student__full_name']

    @action(detail=True, methods=['post'], permission_classes=[IsTenantMember])
    def verify(self, request, pk=None):
        """Mark a document as verified (super_admin / academic_head only)."""
        from apps.common.permissions import _user_role
        role = _user_role(request)
        if role not in ('super_admin', 'academic_head'):
            return Response({'detail': 'Not authorized to verify documents'}, status=403)
        doc = self.get_object()
        doc.status = StudentDoc.STATUS_VERIFIED
        doc.verified_by = request.user.systemuser
        doc.verified_at = doc.verified_at or None
        from django.utils import timezone
        doc.verified_at = timezone.now()
        doc.save()
        return Response(StudentDocSerializer(doc).data)

    @action(detail=True, methods=['post'], permission_classes=[IsTenantMember])
    def reject(self, request, pk=None):
        """Reject a document with a reason."""
        from apps.common.permissions import _user_role
        role = _user_role(request)
        if role not in ('super_admin', 'academic_head'):
            return Response({'detail': 'Not authorized to reject documents'}, status=403)
        doc = self.get_object()
        doc.status = StudentDoc.STATUS_REJECTED
        doc.rejection_reason = request.data.get('reason', 'Rejected by reviewer')
        doc.save()
        return Response(StudentDocSerializer(doc).data)


class EnrollmentViewSet(TenantAwareViewMixin, viewsets.ModelViewSet):
    """
    Enrollment management with Session Enforcement Matrix validation.

    Status transitions are validated against the Enrollment.TRANSITIONS state machine.
    """
    queryset = Enrollment.all_objects.select_related(
        'student', 'course', 'course__university', 'session', 'sub_center'
    )
    serializer_class = EnrollmentSerializer
    permission_classes = [IsCounselorOrAbove]
    filterset_fields = ['sub_center', 'status', 'session', 'course']
    search_fields = ['student__full_name', 'course__name', 'enrollment_number']
    ordering_fields = ['created_at', 'status']

    def get_queryset(self):
        return Enrollment.objects.select_related(
            'student', 'course', 'course__university', 'session', 'sub_center'
        )

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Audit timeline for a specific enrollment."""
        from apps.audit.models import AuditLog
        enrollment = self.get_object()
        logs = AuditLog.objects.filter(
            table_name='enrollments', row_id=enrollment.id
        ).order_by('created_at').values('action_type', 'created_at', 'old_data', 'new_data')
        return Response(list(logs))

    @action(detail=True, methods=['patch'], url_path='status')
    def transition_status(self, request, pk=None):
        """Transition enrollment status with state-machine validation."""
        enrollment = self.get_object()
        serializer = EnrollmentStatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        if not enrollment.can_transition_to(new_status):
            return Response({
                'detail': f'Invalid transition: {enrollment.status} → {new_status}',
                'allowed_transitions': Enrollment.TRANSITIONS.get(enrollment.status, []),
            }, status=400)

        old_status = enrollment.status
        enrollment.status = new_status
        if serializer.validated_data.get('notes'):
            enrollment.notes = enrollment.notes + f"\n[{new_status}] {serializer.validated_data['notes']}"
        enrollment.save()

        # Trigger async notifications (Celery task — eager in dev)
        from apps.notifications.tasks import notify_enrollment_status_change
        notify_enrollment_status_change.delay(str(enrollment.id), old_status, new_status)

        return Response(EnrollmentSerializer(enrollment).data)
