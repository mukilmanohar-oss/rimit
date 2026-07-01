"""
Audit app: audit_logs table (partitioned by created_at in prod).

Per dbschema.md:
  - audit_logs: id (UUID, PK), user_id (FK), action_type (VARCHAR),
                table_name (VARCHAR), row_id (UUID),
                old_data (JSONB), new_data (JSONB), created_at (TIMESTAMP)

In production with PostgreSQL: declarative partitioned monthly via pg_partman.
In dev (SQLite): regular table.
"""
import uuid
from django.db import models
from apps.common.models import UUIDModel


class AuditLog(UUIDModel):
    """Audit trail entry (partitioned by created_at in prod)."""
    user = models.ForeignKey(
        'partners.SystemUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_actions',
    )
    user_email = models.EmailField(blank=True, help_text='Snapshot of user email at action time')
    action_type = models.CharField(max_length=50, db_index=True,
                                    help_text='create | update | delete | status_transition')
    table_name = models.CharField(max_length=100, db_index=True)
    row_id = models.UUIDField(null=True, blank=True, db_index=True)
    old_data = models.JSONField(default=dict, blank=True)
    new_data = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['table_name', 'row_id']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_type} on {self.table_name}:{self.row_id} at {self.created_at}"
