"""Serializers for admissions app."""
import re
from django.db import IntegrityError
from rest_framework import serializers
from apps.admissions.models import Student, StudentAcademicHistory, StudentDoc, Enrollment, StudentAddress
from apps.common.models import hash_aadhar


class StudentAcademicHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAcademicHistory
        fields = ['id', 'student', 'qualification', 'examination', 'institution', 'board_university',
                  'year_of_passing', 'score_type', 'score_value', 'percentage_marks', 'result', 'subject_stream',
                  'created_at', 'updated_at']
        read_only_fields = ('id', 'student', 'created_at', 'updated_at')

class StudentAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAddress
        exclude = ('student', 'created_at', 'updated_at', 'id')


class StudentDocSerializer(serializers.ModelSerializer):
    s3_object_uri = serializers.SerializerMethodField()

    class Meta:
        model = StudentDoc
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'verified_by', 'verified_at', 's3_object_uri', 'file_size_bytes', 'mime_type')

    def get_s3_object_uri(self, obj):
        from apps.common.utils_storage import get_presigned_url
        return get_presigned_url(obj.s3_object_uri)


class StudentSerializer(serializers.ModelSerializer):
    academic_histories = StudentAcademicHistorySerializer(many=True, required=False)
    documents = StudentDocSerializer(many=True, read_only=True)
    address_block = StudentAddressSerializer(required=False)
    aadhar_number = serializers.CharField(write_only=True, required=True,
                                          help_text='Plaintext Aadhar; stored as SHA-256 hash')
    sub_center_code = serializers.CharField(source='sub_center.center_code', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    receipt_s3_url = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'sub_center', 'sub_center_code', 'full_name', 'dob', 'gender',
            'primary_phone', 'email', 'aadhar_number', 'aadhar_hash',
            'category', 'employment_status', 'marital_status', 'religion', 'abc_id', 'deb_id', 'receipt_s3_url',
            'address_block', 'address_data', 'parent_name', 'father_name', 'mother_name', 'parent_phone', 'alternate_phone', 'alternate_email',
            'is_active', 'admission_type', 'admission_semester',
            'course', 'course_name', 'session', 'sub_course', 'lead_owner', 'lead_status',
            'academic_histories', 'documents', 'created_at', 'updated_at',
        ]
        read_only_fields = ('id', 'aadhar_hash', 'sub_center', 'created_at', 'updated_at')

    def get_receipt_s3_url(self, obj):
        if obj.receipt_s3_url:
            from apps.common.utils_storage import get_presigned_url
            return get_presigned_url(obj.receipt_s3_url)
        return None

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
        address_block_data = validated_data.pop('address_block', None)
        academic_histories_data = validated_data.pop('academic_histories', [])

        request = self.context.get('request')
        if request and 'sub_center' not in validated_data:
            from apps.partners.models import SystemUser
            try:
                su = SystemUser.objects.get(user=request.user)
                if su.sub_center_id:
                    validated_data['sub_center'] = su.sub_center
            except SystemUser.DoesNotExist:
                pass

        if 'sub_center' not in validated_data:
            from apps.partners.models import SubCenter
            # Fallback for super_admin testing
            fallback = SubCenter.objects.first()
            if fallback:
                validated_data['sub_center'] = fallback
            else:
                raise serializers.ValidationError(
                    {'sub_center': 'No sub-centers available. Please create one first.'}
                )

        student = Student(**validated_data)
        if aadhar:
            student.set_aadhar(aadhar)

        # Explicit pre-save duplicate check (fast path, returns clean 400).
        # This is the primary guard; the IntegrityError below is a race-condition
        # safety net in case two requests slip through simultaneously.
        if student.aadhar_hash and Student.all_objects.filter(aadhar_hash=student.aadhar_hash).exists():
            raise serializers.ValidationError(
                {'aadhar_number': 'A student with this Aadhar number already exists.'}
            )

        try:
            student.save()
        except IntegrityError as e:
            # Race-condition safety net: DB unique constraint fires.
            if 'aadhar_hash' in str(e).lower():
                raise serializers.ValidationError(
                    {'aadhar_number': 'A student with this Aadhar number already exists.'}
                )
            raise

        if address_block_data:
            StudentAddress.objects.create(student=student, **address_block_data)

        for ah_data in academic_histories_data:
            StudentAcademicHistory.objects.create(student=student, **ah_data)

        return student

    def update(self, instance, validated_data):
        aadhar = validated_data.pop('aadhar_number', None)
        address_block_data = validated_data.pop('address_block', None)
        academic_histories_data = validated_data.pop('academic_histories', None)
        
        if aadhar:
            instance.set_aadhar(aadhar)
            
        if address_block_data is not None:
            if hasattr(instance, 'address_block'):
                for attr, value in address_block_data.items():
                    setattr(instance.address_block, attr, value)
                instance.address_block.save()
            else:
                StudentAddress.objects.create(student=instance, **address_block_data)
                
        if academic_histories_data is not None:
            instance.academic_histories.all().delete()
            for ah_data in academic_histories_data:
                StudentAcademicHistory.objects.create(student=instance, **ah_data)
                
        return super().update(instance, validated_data)


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight list view."""
    sub_center_code = serializers.CharField(source='sub_center.center_code', read_only=True)
    enrollment_count = serializers.SerializerMethodField()
    course_name = serializers.CharField(source='course.name', read_only=True)
    lead_status = serializers.CharField(read_only=True)
    course_total_fee = serializers.SerializerMethodField()
    your_commission = serializers.SerializerMethodField()
    net_payable = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'sub_center_code', 'full_name', 'dob', 'primary_phone',
            'email', 'is_active', 'lead_status', 'course', 'course_name',
            'course_total_fee', 'your_commission', 'net_payable',
            'enrollment_count', 'created_at',
        ]

    def get_enrollment_count(self, obj):
        return obj.enrollments.count()

    def get_course_total_fee(self, obj):
        # Prefer annotated value from queryset to avoid N+1
        v = getattr(obj, 'course_total_fee', None)
        if v is not None:
            return v
        if not obj.course_id:
            return None
        return sum(f.amount for f in obj.course.fees.filter(is_active=True))

    def _calc_breakdown(self, obj):
        if not obj.course_id:
            return None
        total_fee = self.get_course_total_fee(obj) or 0
        course = obj.course
        uni_pct = course.university_share_percent
        if uni_pct is None:
            uni_pct = course.university.default_university_share_percent

        from apps.finance.net_remittance import calculate_net_remittance
        return calculate_net_remittance(
            total_fee=total_fee,
            university_share_percent=uni_pct,
            sub_center_commission_percent=obj.sub_center.commission_percent,
        )

    def get_your_commission(self, obj):
        b = self._calc_breakdown(obj)
        return b.sub_center_commission if b else None

    def get_net_payable(self, obj):
        b = self._calc_breakdown(obj)
        return b.net_payable if b else None


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
                # 1. Eligibility Check (Gap 8)
                eligibility = course.eligibility_criteria_json or {}
                if eligibility:
                    # check if student meets qualification requirements
                    req_qual = eligibility.get('min_qualification')
                    req_score = eligibility.get('min_score_percentage')
                    
                    if req_qual or req_score:
                        histories = student.academic_histories.all()
                        if not histories:
                            raise serializers.ValidationError({'course': 'Student has no academic history to verify eligibility.'})
                        
                        passed_eligibility = False
                        for h in histories:
                            # basic check: if req_qual matches or is not specified, check score
                            if req_qual and h.qualification != req_qual:
                                continue
                            if req_score and h.score_type == 'percentage' and h.score_value < float(req_score):
                                continue
                            passed_eligibility = True
                            break
                        
                        if not passed_eligibility:
                            raise serializers.ValidationError({'course': f'Student does not meet minimum eligibility criteria (Required: {req_qual}, {req_score}%).'})

                # 2. Session Enforcement Matrix
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
    admission_number = serializers.CharField(required=False, allow_blank=True)
    registration_number = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        from apps.admissions.models import Enrollment
        valid = [s[0] for s in Enrollment.STATUS_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(f'Invalid status. Valid: {valid}')
        return value
