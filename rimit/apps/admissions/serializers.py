"""Serializers for admissions app."""
import re
from rest_framework import serializers
from apps.admissions.models import Student, StudentAcademicHistory, StudentDoc, Enrollment
from apps.common.models import hash_aadhar


class StudentAcademicHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAcademicHistory
        fields = ['id', 'student', 'qualification', 'institution', 'board_university',
                  'year_of_passing', 'score_type', 'score_value', 'subject_stream',
                  'created_at', 'updated_at']
        read_only_fields = ('id', 'student', 'created_at', 'updated_at')


class StudentDocSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDoc
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'verified_by', 'verified_at')


class StudentSerializer(serializers.ModelSerializer):
    academic_histories = StudentAcademicHistorySerializer(many=True, read_only=True)
    documents = StudentDocSerializer(many=True, read_only=True)
    aadhar_number = serializers.CharField(write_only=True, required=False, allow_blank=True,
                                          help_text='Plaintext Aadhar; stored as SHA-256 hash')
    sub_center_code = serializers.CharField(source='sub_center.center_code', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'sub_center', 'sub_center_code', 'full_name', 'dob', 'gender',
            'primary_phone', 'email', 'aadhar_number', 'aadhar_hash',
            'address_data', 'parent_name', 'parent_phone', 'is_active',
            'academic_histories', 'documents', 'created_at', 'updated_at',
        ]
        read_only_fields = ('id', 'aadhar_hash', 'sub_center', 'created_at', 'updated_at')

    def validate_primary_phone(self, value):
        """Indian phone format: +91XXXXXXXXXX or 0XXXXXXXXXX or 10 digits."""
        cleaned = re.sub(r'[\s\-()]', '', value)
        if not re.match(r'^(\+91|91|0)?[6-9]\d{9}$', cleaned):
            raise serializers.ValidationError('Invalid Indian phone number format')
        return cleaned

    def validate_aadhar_number(self, value):
        """Aadhar format: 12 digits (with optional spaces)."""
        if not value:
            return value
        cleaned = re.sub(r'\s', '', value)
        if not re.match(r'^\d{12}$', cleaned):
            raise serializers.ValidationError('Aadhar must be 12 digits')
        return cleaned

    def validate_email(self, value):
        if value and not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
            raise serializers.ValidationError('Invalid email format')
        return value

    def create(self, validated_data):
        aadhar = validated_data.pop('aadhar_number', None)
        # Tenant auto-set from current user
        request = self.context.get('request')
        if request and 'sub_center' not in validated_data:
            from apps.partners.models import SystemUser
            try:
                su = SystemUser.objects.get(user=request.user)
                if su.sub_center_id:
                    validated_data['sub_center'] = su.sub_center
            except SystemUser.DoesNotExist:
                pass
        student = Student(**validated_data)
        if aadhar:
            student.set_aadhar(aadhar)
        try:
            student.save()
        except Exception:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError({'aadhar_number': 'A student with this Aadhar number already exists.'})
        return student

    def update(self, instance, validated_data):
        aadhar = validated_data.pop('aadhar_number', None)
        if aadhar:
            instance.set_aadhar(aadhar)
        return super().update(instance, validated_data)


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight list view."""
    sub_center_code = serializers.CharField(source='sub_center.center_code', read_only=True)
    enrollment_count = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'sub_center_code', 'full_name', 'dob', 'primary_phone',
            'email', 'is_active', 'enrollment_count', 'created_at',
        ]

    def get_enrollment_count(self, obj):
        return obj.enrollments.count()


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    university_name = serializers.CharField(source='course.university.name', read_only=True)
    session_name = serializers.CharField(source='session.session_name', read_only=True)
    sub_center_code = serializers.CharField(source='sub_center.center_code', read_only=True)
    next_valid_statuses = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ('id', 'sub_center', 'enrollment_number', 'created_at', 'updated_at')

    def get_next_valid_statuses(self, obj):
        return Enrollment.TRANSITIONS.get(obj.status, [])

    def validate(self, attrs):
        """On create: run Session Enforcement Matrix validation."""
        request = self.context.get('request')
        if request and self.instance is None:
            from apps.rules.engine import validate_enrollment
            student = attrs.get('student')
            course = attrs.get('course')
            session = attrs.get('session')
            if student and course and session:
                # Auto-set sub_center from student if not provided
                if 'sub_center' not in attrs:
                    attrs['sub_center'] = student.sub_center
                result = validate_enrollment(student, course, session)
                if not result.valid:
                    raise serializers.ValidationError({
                        'session': result.reason,
                        'suggested_session': str(result.suggested_session_id) if result.suggested_session_id else None,
                    })
        return attrs


class EnrollmentStatusTransitionSerializer(serializers.Serializer):
    """Serializer for status transition PATCH."""
    status = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        from apps.admissions.models import Enrollment
        valid = [s[0] for s in Enrollment.STATUS_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(f'Invalid status. Valid: {valid}')
        return value
