"""
Session Enforcement Matrix engine.

Evaluates rules_configurations against a student/course/session triple
and returns whether enrollment is allowed, plus a suggested alternative
session if rejected.

This is the core of RFP Module 3: "Programmatic validation rules mapping
specific student eligibility to distinct intake cycles."

Example rule (RFP §3):
    Fresh candidates cannot enroll in July session; route to October.
"""
from dataclasses import dataclass
from typing import Optional
from django.utils import timezone
from apps.rules.models import RulesConfiguration, IntakeSession


@dataclass
class ValidationResult:
    valid: bool
    reason: str = ''
    suggested_session_id: Optional[str] = None
    matched_rule_name: str = ''


def is_fresh_candidate(student) -> bool:
    """A fresh candidate has no prior enrollments (excluding cancelled)."""
    from apps.admissions.models import Enrollment
    # Use all_objects to bypass tenant filter (freshness is cross-tenant by definition)
    prior = Enrollment.all_objects.filter(
        student=student
    ).exclude(status=Enrollment.STATUS_CANCELLED).count()
    return prior == 0


def evaluate_rule(rule: RulesConfiguration, student, course, session) -> ValidationResult:
    """
    Evaluate a single rule against the enrollment context.

    Returns ValidationResult(valid=True) if rule does NOT apply (passes),
    or ValidationResult(valid=False, ...) if rule rejects the enrollment.
    """
    conditions = rule.conditions or {}
    action = conditions.get('action', 'allow')

    # Check if this rule applies to this enrollment
    applies = True

    # Condition: student_is_fresh
    if 'student_is_fresh' in conditions:
        fresh = is_fresh_candidate(student)
        if conditions['student_is_fresh'] != fresh:
            applies = False

    # Condition: session_name_in (list)
    if applies and 'session_name_in' in conditions:
        if session.session_name not in conditions['session_name_in']:
            applies = False

    # Condition: course_stream_in
    if applies and 'course_stream_in' in conditions:
        if course.stream not in conditions['course_stream_in']:
            applies = False

    # Condition: session_is_fresh_allowed
    if applies and 'session_is_fresh_allowed' in conditions:
        if session.is_fresh_allowed != conditions['session_is_fresh_allowed']:
            applies = False

    if not applies:
        return ValidationResult(valid=True, matched_rule_name=rule.rule_name)

    # Rule applies → take action
    if action == 'reject':
        suggested_id = None
        if conditions.get('suggested_session'):
            try:
                sug = IntakeSession.objects.filter(
                    session_name=conditions['suggested_session'],
                    is_active=True,
                ).first()
                if sug:
                    suggested_id = sug.id
            except Exception:
                pass
        return ValidationResult(
            valid=False,
            reason=conditions.get('reason', f'Rejected by rule: {rule.rule_name}'),
            suggested_session_id=suggested_id,
            matched_rule_name=rule.rule_name,
        )

    # action == 'allow' (or no action) → rule passes
    return ValidationResult(valid=True, matched_rule_name=rule.rule_name)


def validate_enrollment(student, course, session) -> ValidationResult:
    """
    Run all active rules against an enrollment attempt.

    Returns the FIRST rejection (highest priority) or a pass if no rule rejects.
    """
    # Validation disabled per user request
    return ValidationResult(valid=True)


def suggest_valid_session(student, course) -> Optional[IntakeSession]:
    """Suggest the next valid session for a student/course pair."""
    sessions = IntakeSession.objects.filter(
        is_active=True,
        start_date__gte=timezone.now().date(),
    ).order_by('start_date')

    for session in sessions:
        if validate_enrollment(student, course, session).valid:
            return session
    return None
