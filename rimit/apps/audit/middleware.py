"""
Audit middleware: auto-logs state-changing operations.

Hooks into DRF ViewSet perform_create / perform_update / perform_destroy
via a mixin (preferred) OR via middleware that inspects responses.

This implementation provides:
  1. AuditLogMiddleware - lightweight, logs HTTP method + path + user
  2. AuditLogMixin - to be added to ViewSets for before/after diff logging
"""
import json
import logging
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogMiddleware:
    """Log all non-GET requests to audit_logs (lightweight, no diff)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only log state-changing methods
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            try:
                user_email = ''
                user_id = None
                if request.user.is_authenticated:
                    user_email = request.user.email
                    try:
                        from apps.partners.models import SystemUser
                        su = SystemUser.objects.get(user=request.user)
                        user_id = su.id
                    except SystemUser.DoesNotExist:
                        pass

                AuditLog.objects.create(
                    user_id=user_id,
                    user_email=user_email,
                    action_type=request.method.lower(),
                    table_name=request.path.split('/')[3] if len(request.path.split('/')) > 3 else 'unknown',
                    row_id=None,  # Populated by AuditLogMixin in ViewSets
                    old_data={},
                    new_data={},
                    ip_address=self._get_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                )
            except Exception as e:
                logger.warning(f'Audit log write failed: {e}')

        return response

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class AuditLogMixin:
    """
    Mixin for ViewSets to capture before/after diffs.

    Usage:
        class StudentViewSet(AuditLogMixin, viewsets.ModelViewSet):
            AUDIT_TABLE = 'students'
    """
    AUDIT_TABLE = None

    def _write_audit(self, action_type, instance, old_data=None):
        try:
            from rest_framework import serializers
            from apps.common.middleware import _current_user_id
            from apps.partners.models import SystemUser

            user_id = _current_user_id()
            su = None
            if user_id:
                try:
                    su = SystemUser.objects.get(user_id=user_id)
                except SystemUser.DoesNotExist:
                    pass

            new_data = {}
            if instance:
                # Use the ViewSet's serializer to snapshot the new state
                try:
                    new_data = self.get_serializer(instance).data
                    new_data = {k: (str(v) if v else v) for k, v in new_data.items()}
                except Exception:
                    pass

            AuditLog.objects.create(
                user=su,
                user_email=getattr(su, 'email', '') if su else '',
                action_type=action_type,
                table_name=self.AUDIT_TABLE or self.queryset.model._meta.db_table,
                row_id=getattr(instance, 'id', None),
                old_data=old_data or {},
                new_data=new_data,
            )
        except Exception as e:
            logger.warning(f'AuditLogMixin write failed: {e}')

    def _snapshot(self, instance):
        """Capture current state for diff."""
        if not instance:
            return {}
        try:
            data = self.get_serializer(instance).data
            return {k: (str(v) if v else v) for k, v in data.items()}
        except Exception:
            return {}

    def perform_create(self, serializer):
        instance = serializer.save()
        self._write_audit('create', instance)
        return instance

    def perform_update(self, serializer):
        old_data = self._snapshot(serializer.instance)
        instance = serializer.save()
        self._write_audit('update', instance, old_data)
        return instance

    def perform_destroy(self, instance):
        old_data = self._snapshot(instance)
        instance_id = instance.id
        instance.delete()
        self._write_audit('delete', type('Stub', (), {'id': instance_id})(), old_data)
