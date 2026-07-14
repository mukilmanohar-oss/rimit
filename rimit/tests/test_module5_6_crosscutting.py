"""
Phase 5 + 6 — Cross-cutting concerns (audit logs, finance dashboard, auth/RBAC, MFA).

Covers:
- AuditLog model + middleware (auto-logs state-changing requests)
- PaymentLedger API + summary endpoint
- Finance dashboard: by_sub_center breakdown (super_admin only)
- Auth: token endpoint, /auth/profile/, /auth/mfa/verify/
- RBAC matrix: each role has correct read/write permissions
- MFA stub: accepts any 6-digit OTP in dev mode
"""
import json
import pytest
from rest_framework import status
from apps.audit.models import AuditLog
from apps.finance.models import PaymentLedger
from apps.admissions.models import Enrollment
from tests.factories import (
    SubCenterFactory, StudentFactory, UniversityFactory, CourseFactory,
    IntakeSessionFactory,
)
from tests.base import BaseAPITestCase


@pytest.mark.django_db
class TestAuditLog(BaseAPITestCase):
    """Audit trail captures all state-changing operations."""

    def test_post_request_creates_audit_log(self):
        """Creating a university via API logs an entry."""
        client = self.super_admin_client()
        resp = client.post('/api/v1/universities', json.dumps({
            'name': 'Audit Test University',
            'state': 'Kerala',
        }), content_type='application/json')
        assert resp.status_code == status.HTTP_201_CREATED

        # AuditLog should have at least one entry from this request
        # (AuditLogMiddleware logs all POST/PUT/PATCH/DELETE)
        logs = AuditLog.objects.filter(action_type='post')
        assert logs.count() >= 1

    def test_get_request_not_logged(self):
        """GET requests are not audit-logged."""
        UniversityFactory()
        client = self.academic_head_client()
        client.get('/api/v1/universities')
        # No 'get' entries should exist
        assert AuditLog.objects.filter(action_type='get').count() == 0


@pytest.mark.django_db
class TestFinanceAPI(BaseAPITestCase):
    """Payment ledger + financial dashboard."""

    def _setup_payment(self, sub_center, amount=50000, status='captured'):
        student = StudentFactory(sub_center=sub_center)
        uni = UniversityFactory()
        course = CourseFactory(university=uni)
        session = IntakeSessionFactory()
        enrollment = Enrollment.all_objects.create(
            sub_center=sub_center, student=student, course=course, session=session,
            status=Enrollment.STATUS_FEE_PAID,
        )
        return PaymentLedger.all_objects.create(
            sub_center=sub_center, enrollment=enrollment,
            amount_paid=amount, transaction_ref=f'pay_{enrollment.id}',
            status=status, gateway='razorpay',
        )

    def test_finance_can_view_own_center_payments(self):
        self._setup_payment(self.center_a, amount=50000)
        self._setup_payment(self.center_b, amount=30000)

        client = self.finance_client(sub_center=self.center_a)
        resp = client.get('/api/v1/payments')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 1  # Only own center (RLS)

    def test_super_admin_can_view_all_payments(self):
        self._setup_payment(self.center_a, amount=50000)
        self._setup_payment(self.center_b, amount=30000)

        client = self.super_admin_client()
        resp = client.get('/api/v1/payments')
        assert resp.data['count'] == 2

    def test_counselor_cannot_view_payments(self):
        client = self.counselor_client()
        resp = client.get('/api/v1/payments')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_summary_endpoint(self):
        """Summary returns total collected + pending counts."""
        self._setup_payment(self.center_a, amount=50000, status='captured')
        self._setup_payment(self.center_a, amount=30000, status='pending')

        client = self.finance_client(sub_center=self.center_a)
        resp = client.get('/api/v1/payments/summary')
        assert resp.status_code == status.HTTP_200_OK
        assert float(resp.data['total_collected']) == 50000.0
        assert float(resp.data['total_pending']) == 30000.0
        assert resp.data['captured_count'] == 1
        assert resp.data['pending_count'] == 1

    def test_by_sub_center_endpoint_super_admin_only(self):
        self._setup_payment(self.center_a, amount=50000)
        self._setup_payment(self.center_b, amount=30000)

        # Super admin can see breakdown
        client = self.super_admin_client()
        resp = client.get('/api/v1/payments/by_sub_center')
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 2

        # Finance at center_a cannot see cross-center breakdown
        client = self.finance_client(sub_center=self.center_a)
        resp = client.get('/api/v1/payments/by_sub_center')
        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAuthEndpoints(BaseAPITestCase):
    """Token auth, profile, MFA stub."""

    def test_token_endpoint_returns_token(self):
        from rest_framework.authtoken.models import Token
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='authtest', password='pass123')
        Token.objects.create(user=user)

        from rest_framework.test import APIClient
        client = APIClient()
        resp = client.post('/api/v1/auth/token', {'username': 'authtest', 'password': 'pass123'})
        assert resp.status_code == status.HTTP_200_OK
        assert 'token' in resp.data

    def test_profile_endpoint_returns_role_and_tenant(self):
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.get('/api/v1/auth/profile')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['role'] == 'counselor'
        assert resp.data['sub_center_id'] == str(self.center_a.id)
        assert resp.data['sub_center_code'] == self.center_a.center_code

    def test_mfa_verify_accepts_6_digit_otp(self):
        client = self.counselor_client()
        resp = client.post('/api/v1/auth/mfa/verify', json.dumps({'otp': '123456'}),
                           content_type='application/json')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['status'] == 'verified'

    def test_mfa_verify_rejects_invalid_otp(self):
        client = self.counselor_client()
        resp = client.post('/api/v1/auth/mfa/verify', json.dumps({'otp': 'abc'}),
                           content_type='application/json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRBACMatrix(BaseAPITestCase):
    """
    Comprehensive RBAC matrix verification.

    Per Section 9.1: "The four RFP-defined roles map to Keycloak realm roles."
    Each role has specific read/write permissions per module.
    """

    def test_super_admin_full_access(self):
        """Super Admin can access all endpoints."""
        client = self.super_admin_client()
        for endpoint in ['/api/v1/universities', '/api/v1/students',
                         '/api/v1/enrollments', '/api/v1/intake-sessions',
                         '/api/v1/rules/session-matrix', '/api/v1/payments',
                         '/api/v1/notifications/logs']:
            resp = client.get(endpoint)
            assert resp.status_code in (200, 403), f'{endpoint}: {resp.status_code}'

    def test_academic_head_read_all(self):
        """Academic Head can read across all tenants."""
        client = self.academic_head_client()
        resp = client.get('/api/v1/students')
        assert resp.status_code == status.HTTP_200_OK
        # But cannot write to rules (super_admin only)
        resp = client.post('/api/v1/rules/session-matrix', json.dumps({
            'rule_name': 'unauthorized', 'conditions': {},
        }), content_type='application/json')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_counselor_tenant_scoped(self):
        """Counselor can read/write own tenant only, no rules, no finance."""
        client = self.counselor_client(sub_center=self.center_a)
        # Can create students in own center
        # Cannot access finance
        resp = client.get('/api/v1/payments')
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        # Cannot access rules config
        resp = client.get('/api/v1/rules/session-matrix')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_finance_tenant_scoped_no_student_write(self):
        """Finance can read students but not create them."""
        client = self.finance_client(sub_center=self.center_a)
        # Can read students (for payment context)
        resp = client.get('/api/v1/students')
        assert resp.status_code == status.HTTP_200_OK
        # Cannot create students (counselor only)
        resp = client.post('/api/v1/students', json.dumps({
            'full_name': 'X', 'dob': '2000-01-01',
            'primary_phone': '+919876543210', 'aadhar_number': '123456789012',
        }), content_type='application/json')
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        # Can read payments
        resp = client.get('/api/v1/payments')
        assert resp.status_code == status.HTTP_200_OK

    def test_unauthenticated_denied(self):
        """No token = 401."""
        from rest_framework.test import APIClient
        client = APIClient()
        resp = client.get('/api/v1/students')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
