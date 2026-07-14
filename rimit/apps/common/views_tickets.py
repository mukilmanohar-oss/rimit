
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.common.models import Ticket, TicketReply
from apps.common.middleware import _current_tenant_id
from apps.common.permissions import _user_role
from rest_framework.exceptions import PermissionDenied

class TicketViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from apps.common.serializers_tickets import TicketSerializer
        return TicketSerializer

    def get_queryset(self):
        user = self.request.user
        role = _user_role(self.request)
        tenant_id = _current_tenant_id()
        
        if role in ('super_admin', 'academic_head'):
            return Ticket.objects.all()
        else:
            return Ticket.objects.filter(sub_center_id=tenant_id)

    def perform_create(self, serializer):
        tenant_id = _current_tenant_id()
        serializer.save(created_by=self.request.user, sub_center_id=tenant_id)

    @action(detail=True, methods=['post'])
    def add_reply(self, request, pk=None):
        ticket = self.get_object()
        message = request.data.get('message')
        if not message:
            return Response({'error': 'Message is required'}, status=400)
            
        is_admin_reply = request.data.get('is_admin_reply', False)
        if is_admin_reply and _user_role(request) not in ('super_admin', 'academic_head'):
            return Response({'error': 'Only admins can post admin replies'}, status=403)
            
        reply = TicketReply.objects.create(
            ticket=ticket,
            sender=request.user,
            message=message,
            is_admin_reply=is_admin_reply
        )
        
        from apps.common.serializers_tickets import TicketReplySerializer
        return Response(TicketReplySerializer(reply).data)
