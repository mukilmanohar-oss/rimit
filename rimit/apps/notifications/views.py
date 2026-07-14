"""ViewSets for notifications app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.common.permissions import IsSuperAdmin, IsSuperAdminOrReadOnly, IsTenantMember, IsFinanceOrAbove
from apps.common.rbac import ResourcePermission
from apps.notifications.models import NotificationLog
from apps.notifications.serializers import NotificationLogSerializer, BroadcastSerializer


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only notification logs. Visible to finance+ only (operational data)."""
    queryset = NotificationLog.objects.all()
    serializer_class = NotificationLogSerializer
    resource_name = 'notification'
    permission_classes = [ResourcePermission]
    filterset_fields = ['channel', 'delivery_status', 'template_id']
    ordering_fields = ['created_at', 'delivery_status']


class BroadcastView(APIView):
    """Broadcast a notification to a list of recipients."""
    resource_name = 'notification' # Though only 'create' maps to 'broadcast' basically, let's keep it simple
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        serializer = BroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.notifications.tasks import broadcast_notification
        task = broadcast_notification.delay(
            recipient_list=serializer.validated_data['recipients'],
            channel=serializer.validated_data['channel'],
            template_id=serializer.validated_data['template_id'],
            context=serializer.validated_data.get('context', {}),
        )
        return Response({'task_id': task.id, 'queued': len(serializer.validated_data['recipients'])})
