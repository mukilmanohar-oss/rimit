"""Read-only ViewSet for LeadIngestionLog monitoring."""
from rest_framework import viewsets, serializers
from apps.common.permissions import IsSuperAdmin
from apps.integrations.models import LeadIngestionLog


class LeadIngestionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadIngestionLog
        fields = '__all__'


class LeadIngestionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only monitoring of inbound leads from Meta/Google/Referral."""
    queryset = LeadIngestionLog.objects.all()
    serializer_class = LeadIngestionLogSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['source', 'status', 'campaign_id']
    search_fields = ['leadgen_id', 'campaign_id']
    ordering_fields = ['created_at', 'status']
