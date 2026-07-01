"""Serializers for notifications app."""
from rest_framework import serializers
from apps.notifications.models import NotificationLog


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'external_message_id', 'delivery_status', 'retry_count', 'error_msg')


class BroadcastSerializer(serializers.Serializer):
    recipients = serializers.ListField(child=serializers.CharField(), min_length=1, max_length=10000)
    channel = serializers.ChoiceField(choices=['whatsapp', 'sms', 'email'])
    template_id = serializers.CharField(max_length=100)
    context = serializers.JSONField(required=False, default=dict)
