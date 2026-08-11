"""Serializers for finance app."""
from rest_framework import serializers
from apps.finance.models import PaymentLedger


class PaymentLedgerSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='enrollment.student.full_name', read_only=True)
    course_name = serializers.CharField(source='enrollment.course.name', read_only=True)
    sub_center_code = serializers.CharField(source='sub_center.center_code', read_only=True)
    screenshot_uri = serializers.SerializerMethodField()

    class Meta:
        model = PaymentLedger
        fields = '__all__'
        read_only_fields = ('id', 'sub_center', 'gateway_response', 'receipt_uri', 'created_at', 'updated_at')

    def get_screenshot_uri(self, obj):
        if obj.screenshot_uri:
            from apps.common.utils_storage import get_presigned_url
            return get_presigned_url(obj.screenshot_uri)
        return ""


class BatchCheckoutSerializer(serializers.Serializer):
    """Validate payload for /checkout/batch/ endpoint."""
    student_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text='Array of student UUIDs (must all belong to the same sub-center and be Pending Payment).',
    )
