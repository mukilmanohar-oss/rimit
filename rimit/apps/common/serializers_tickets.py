
from rest_framework import serializers
from apps.common.models import Ticket, TicketReply

class TicketReplySerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)

    class Meta:
        model = TicketReply
        fields = ['id', 'ticket', 'sender', 'sender_name', 'message', 'is_admin_reply', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']

class TicketSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    replies = TicketReplySerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'sub_center', 'subject', 'description', 'category', 'status', 'escalation_level', 'created_by', 'created_by_name', 'assigned_to', 'assigned_to_name', 'replies', 'created_at', 'updated_at']
        read_only_fields = ['id', 'sub_center', 'created_by', 'created_at', 'updated_at']
