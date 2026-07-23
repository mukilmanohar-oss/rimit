"""Serializers for aggregator app."""
from rest_framework import serializers
from apps.aggregator.models import University, Course, FeeStructure, UniversityDocVault


class FeeStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructure
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class CourseSerializer(serializers.ModelSerializer):
    fees = FeeStructureSerializer(many=True, read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate(self, attrs):
        is_create = self.instance is None

        # ----------------------------------------------------
        # Rule 1: Name Uniqueness (Per University, Case-Insensitive)
        # ----------------------------------------------------
        name = attrs.get('name')
        university = attrs.get('university')

        # Clean/strip name if provided
        if name is not None:
            cleaned_name = name.strip()
            if not cleaned_name:
                raise serializers.ValidationError({"name": "Course name cannot be blank."})
            attrs['name'] = cleaned_name
            name = cleaned_name

        # Fallback to existing instance values if not provided in the patch payload
        if self.instance:
            if name is None:
                name = self.instance.name
            if university is None:
                university = self.instance.university

        if name and university:
            duplicate_qs = Course.objects.filter(
                name__iexact=name,
                university=university
            )
            if self.instance:
                duplicate_qs = duplicate_qs.exclude(id=self.instance.id)
            
            if duplicate_qs.exists():
                raise serializers.ValidationError({
                    "name": "A course with this name already exists under this university."
                })

        # ----------------------------------------------------
        # Rule 2: University Share Percentage (using attrs)
        # ----------------------------------------------------
        if is_create:
            # Required and cannot be null on creation
            share_pct = attrs.get('university_share_percent')
            if share_pct is None:
                raise serializers.ValidationError({
                    "university_share_percent": "University share percentage override is required."
                })
        else:
            # On update: reject explicitly if present and null
            if 'university_share_percent' in attrs:
                share_pct_val = attrs.get('university_share_percent')
                if share_pct_val is None:
                    raise serializers.ValidationError({
                        'university_share_percent': 'university_share_percent cannot be null on update.'
                    })

        # ----------------------------------------------------
        # Rule 3: Stream Reclassification (using attrs & database state)
        # ----------------------------------------------------
        if not is_create:
            # Force reclassification: if the resulting stream is 'Other', reject.
            current_stream = attrs.get('stream', self.instance.stream)
            if current_stream == 'Other':
                raise serializers.ValidationError({
                    'stream': 'Courses with stream "Other" must be reclassified to a valid stream on update.'
                })

        # ----------------------------------------------------
        # Rule 4: Duration Months (Enforce > 0 if present)
        # ----------------------------------------------------
        # Enforce duration_months > 0 if key is present in attrs (Option A)
        if 'duration_months' in attrs:
            duration = attrs.get('duration_months')
            if duration is None or duration <= 0:
                raise serializers.ValidationError({
                    'duration_months': 'duration_months must be greater than 0.'
                })

        return attrs


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for list view."""
    fees = FeeStructureSerializer(many=True, read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)
    university_state = serializers.CharField(source='university.state', read_only=True)
    total_fee = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'name', 'stream', 'duration_months', 'is_active',
            'university', 'university_name', 'university_state',
            'eligibility_text', 'total_fee', 'fees', 'created_at',
        ]

    def get_total_fee(self, obj):
        return sum(f.amount for f in obj.fees.filter(is_active=True))


class UniversityDocVaultSerializer(serializers.ModelSerializer):
    university_name = serializers.CharField(source='university.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    s3_object_uri = serializers.SerializerMethodField()

    class Meta:
        model = UniversityDocVault
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'uploaded_by', 's3_object_uri', 'file_size_bytes', 'mime_type')

    def get_s3_object_uri(self, obj):
        from apps.common.utils_storage import get_presigned_url
        return get_presigned_url(obj.s3_object_uri)

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                from apps.partners.models import SystemUser
                su = SystemUser.objects.get(user=request.user)
                validated_data['uploaded_by'] = su
            except SystemUser.DoesNotExist:
                pass
        return super().create(validated_data)


class UniversitySerializer(serializers.ModelSerializer):
    course_count = serializers.SerializerMethodField()

    class Meta:
        model = University
        fields = ['id', 'name', 'state', 'accreditation', 'description', 'website',
                  'logo_uri', 'is_active', 'course_count', 'default_university_share_percent', 'created_at', 'updated_at']
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_course_count(self, obj):
        return obj.courses.filter(is_active=True).count()


class UniversityDetailSerializer(UniversitySerializer):
    courses = CourseSerializer(many=True, read_only=True)
    documents = UniversityDocVaultSerializer(many=True, read_only=True)

    class Meta(UniversitySerializer.Meta):
        fields = UniversitySerializer.Meta.fields + ['courses', 'documents']


class CourseCommissionBreakdownSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    course_name = serializers.CharField()
    university_name = serializers.CharField()
    total_course_fee = serializers.DecimalField(max_digits=12, decimal_places=2)
    university_share = serializers.DecimalField(max_digits=12, decimal_places=2)
    university_share_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    default_university_share_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    course_specific_university_share_percent = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    gross_commission_pool = serializers.DecimalField(max_digits=12, decimal_places=2)
    sub_center_commission = serializers.DecimalField(max_digits=12, decimal_places=2)
    sub_center_commission_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    rimit_commission = serializers.DecimalField(max_digits=12, decimal_places=2)
    amount_payable_to_university = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_payable = serializers.DecimalField(max_digits=12, decimal_places=2)

