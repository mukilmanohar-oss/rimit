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


class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view (no nested fees)."""
    university_name = serializers.CharField(source='university.name', read_only=True)
    university_state = serializers.CharField(source='university.state', read_only=True)
    total_fee = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'name', 'stream', 'duration_months', 'is_active',
            'university', 'university_name', 'university_state',
            'eligibility_text', 'total_fee', 'created_at',
        ]

    def get_total_fee(self, obj):
        return sum(f.amount for f in obj.fees.filter(is_active=True))


class UniversityDocVaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniversityDocVault
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'uploaded_by')

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
                  'logo_uri', 'is_active', 'course_count', 'created_at', 'updated_at']
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_course_count(self, obj):
        return obj.courses.filter(is_active=True).count()


class UniversityDetailSerializer(UniversitySerializer):
    courses = CourseSerializer(many=True, read_only=True)
    documents = UniversityDocVaultSerializer(many=True, read_only=True)

    class Meta(UniversitySerializer.Meta):
        fields = UniversitySerializer.Meta.fields + ['courses', 'documents']
