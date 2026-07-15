"""ViewSets for admissions app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.permissions import IsCounselorOrAbove, IsTenantMember, IsFinanceOrAbove, IsSuperAdminOrReadOnly
from apps.common.rbac import ResourcePermission
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
    resource_name = 'student'
    permission_classes = [ResourcePermission]
    filterset_fields = ['sub_center', 'is_active', 'gender', 'lead_status']
    search_fields = ['full_name', 'primary_phone', 'email', 'parent_name']
    ordering_fields = ['full_name', 'created_at', 'dob']
    ordering = ('-created_at', 'id')


    def get_queryset(self):
        from django.db.models import Q, Sum
        return (
            Student.objects
            .select_related('sub_center', 'course', 'course__university')
            .annotate(
                course_total_fee=Sum('course__fees__amount', filter=Q(course__fees__is_active=True))
            )
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        return StudentSerializer

    @action(detail=False, methods=['get'], url_path='check-aadhar')
    def check_aadhar(self, request):
        """Proactively check if a student with this Aadhar number exists."""
        aadhar = request.query_params.get('aadhar')
        if not aadhar:
            return Response({'exists': False})
        from apps.common.models import hash_aadhar
        h = hash_aadhar(aadhar)
        # Use all_objects to prevent sub-center bypass check from leaking duplicates across other sub-centers
        exists = Student.all_objects.filter(aadhar_hash=h).exists()
        return Response({'exists': exists})

    @action(detail=True, methods=['post'], permission_classes=[ResourcePermission])
    def academic_histories(self, request, pk=None):
        """Add an academic history entry to a student."""
        student = self.get_object()
        serializer = StudentAcademicHistorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(student=student)
        return Response(serializer.data, status=201)

    @action(detail=False, methods=['post'], url_path='convert-lead', permission_classes=[ResourcePermission])
    def convert_lead(self, request):
        """Convert a LeadIngestionLog into a Student record (Gap 6)."""
        lead_id = request.data.get('lead_id')
        if not lead_id:
            return Response({'detail': 'lead_id is required'}, status=400)
            
        from apps.integrations.models import LeadIngestionLog
        try:
            lead = LeadIngestionLog.objects.get(id=lead_id)
            if lead.status == LeadIngestionLog.STATUS_CONVERTED:
                return Response({'detail': 'Lead already converted'}, status=400)
        except LeadIngestionLog.DoesNotExist:
            return Response({'detail': 'Lead not found'}, status=404)

        # map normalized_data to student fields
        data = lead.normalized_data or {}
        student_data = {
            'full_name': data.get('full_name') or data.get('name') or 'Unknown Lead',
            'email': data.get('email', ''),
            'primary_phone': data.get('phone_number') or data.get('phone') or '',
            # Mock DOB if missing
            'dob': data.get('dob', '2000-01-01'),
        }

        # Let the serializer handle validation (phone format, etc.)
        serializer = self.get_serializer(data=student_data)
        if serializer.is_valid():
            student = serializer.save()
            lead.status = LeadIngestionLog.STATUS_CONVERTED
            lead.converted_student = student
            lead.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class StudentAcademicHistoryViewSet(TenantAwareViewMixin, viewsets.ModelViewSet):
    queryset = StudentAcademicHistory.objects.select_related('student')
    serializer_class = StudentAcademicHistorySerializer
    resource_name = 'academic_history'
    permission_classes = [ResourcePermission]
    filterset_fields = ['student', 'qualification']


class StudentDocViewSet(TenantAwareViewMixin, viewsets.ModelViewSet):
    """
    Document upload vault for students.

    Accepts multipart uploads (10-100MB per RFP).
    In prod, file is spooled to disk via TemporaryFileUploadHandler
    then uploaded to MinIO by a Celery task.
    """
    queryset = StudentDoc.objects.select_related('student')
    serializer_class = StudentDocSerializer
    resource_name = 'student_doc'
    permission_classes = [ResourcePermission]
    filterset_fields = ['student', 'status']
    search_fields = ['title', 'student__full_name']

    @action(detail=True, methods=['post'], permission_classes=[ResourcePermission])
    def verify(self, request, pk=None):
        """Mark a document as verified (super_admin / academic_head only)."""
        doc = self.get_object()
        doc.status = StudentDoc.STATUS_VERIFIED
        try:
            doc.verified_by = request.user.systemuser
        except Exception:
            doc.verified_by = None  # superuser with no SystemUser record
        from django.utils import timezone
        doc.verified_at = timezone.now()
        doc.save()
        return Response(StudentDocSerializer(doc).data)

    @action(detail=True, methods=['post'], permission_classes=[ResourcePermission])
    def reject(self, request, pk=None):
        """Reject a document with a reason."""
        doc = self.get_object()
        doc.status = StudentDoc.STATUS_REJECTED
        doc.rejection_reason = request.data.get('reason', 'Rejected by reviewer')
        doc.save()
        return Response(StudentDocSerializer(doc).data)


from apps.audit.middleware import AuditLogMixin

class EnrollmentViewSet(AuditLogMixin, TenantAwareViewMixin, viewsets.ModelViewSet):
    """
    Enrollment management with Session Enforcement Matrix validation.

    Status transitions are validated against the Enrollment.TRANSITIONS state machine.
    """
    queryset = Enrollment.all_objects.select_related(
        'student', 'course', 'course__university', 'session', 'sub_center'
    )
    serializer_class = EnrollmentSerializer
    resource_name = 'enrollment'
    permission_classes = [ResourcePermission]
    filterset_fields = ['sub_center', 'status', 'session', 'course', 'admission_type']
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
        """Transition enrollment status with state-machine validation and RBAC."""
        enrollment = self.get_object()
        serializer = EnrollmentStatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        if not enrollment.can_transition_to(new_status):
            return Response({
                'detail': f'Invalid transition: {enrollment.status} → {new_status}',
                'allowed_transitions': Enrollment.TRANSITIONS.get(enrollment.status, []),
            }, status=400)

        # RBAC: determine caller's role
        from apps.common.permissions import _user_role
        role = _user_role(request)

        # Counselors can only move to Document Verified or Cancelled
        if role == 'counselor':
            if new_status not in [Enrollment.STATUS_DOC_VERIFIED, Enrollment.STATUS_CANCELLED]:
                return Response({'detail': 'Counselors cannot manually transition past Document Verified.'}, status=403)

        # Super-admin-only statuses: Fee Paid, Enrolled, Enrollment Generated
        if new_status in Enrollment.SUPER_ADMIN_ONLY_STATUSES:
            if role != 'super_admin':
                return Response({
                    'detail': f'Only Super Admin can transition to "{new_status}".'
                }, status=403)

        old_status = enrollment.status
        old_data = self._snapshot(enrollment) if hasattr(self, '_snapshot') else {}
        enrollment.status = new_status

        # Store admission number when transitioning to Enrolled
        admission_number = serializer.validated_data.get('admission_number', '')
        if new_status == Enrollment.STATUS_ENROLLED and admission_number:
            enrollment.admission_number = admission_number

        # Store registration number when transitioning to Enrollment Generated
        registration_number = serializer.validated_data.get('registration_number', '')
        if new_status == Enrollment.STATUS_ENROLLMENT_GENERATED and registration_number:
            enrollment.registration_number = registration_number

        if serializer.validated_data.get('notes'):
            enrollment.notes = enrollment.notes + f"\n[{new_status}] {serializer.validated_data['notes']}"
        from django.core.exceptions import ValidationError
        try:
            enrollment.save()
        except ValidationError as e:
            return Response(
                e.message_dict if hasattr(e, 'message_dict') else {'detail': e.messages},
                status=400
            )
        # Write audit log explicitly since we bypassed perform_update
        if hasattr(self, '_write_audit'):
            self._write_audit(f'transition to {new_status}', enrollment, old_data=old_data)

        # Trigger async notifications (Celery task — eager in dev)
        from apps.notifications.tasks import notify_enrollment_status_change
        notify_enrollment_status_change.delay(str(enrollment.id), old_status, new_status)

        return Response(EnrollmentSerializer(enrollment).data)

