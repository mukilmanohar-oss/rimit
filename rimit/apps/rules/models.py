"""
Module 3: Advanced Business Logic & Intake Controls.

Models: intake_sessions, rules_configurations.
Engine: Session Enforcement Matrix evaluator (rules_engine.py).
"""
import uuid
from django.db import models
from apps.common.models import UUIDModel, TimeStampedModel


class IntakeSession(UUIDModel, TimeStampedModel):
    """
    Enrollment window (e.g., 'July 2026', 'October 2026').

    Per dbschema.md:
      - id (UUID, PK)
      - session_name (VARCHAR)
      - start_date (DATE)
      - is_active (BOOLEAN)
    """
    session_name = models.CharField(max_length=100, unique=True, db_index=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_fresh_allowed = models.BooleanField(
        default=True,
        help_text='Whether fresh candidates (no prior enrollment) can enroll in this session'
    )

    class Meta:
        db_table = 'intake_sessions'
        ordering = ['-start_date']

    def __str__(self):
        return self.session_name


class RulesConfiguration(UUIDModel, TimeStampedModel):
    """
    JSONB-stored business rule for Session Enforcement Matrix.

    Per dbschema.md:
      - id (UUID, PK)
      - rule_name (VARCHAR)
      - conditions (JSONB)
      - is_active (BOOLEAN)

    Example conditions:
        {
            "student_is_fresh": true,
            "session_name_in": ["July 2026"],
            "action": "reject",
            "suggested_session": "October 2026",
            "reason": "Fresh candidates cannot enroll in July session; route to October."
        }
    """
    rule_name = models.CharField(max_length=200, unique=True, db_index=True)
    description = models.TextField(blank=True)
    conditions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(default=100, help_text='Lower = higher priority')

    class Meta:
        db_table = 'rules_configurations'
        ordering = ['priority', 'rule_name']

    def __str__(self):
        return f"{self.rule_name} (priority={self.priority})"
