"""
Phase 7 — Integration tests: end-to-end workflows + OpenAPI schema validation.

Covers:
- Full enrollment lifecycle: student registration → document upload →
  enrollment create → status transitions → payment webhook → receipt notification
- OpenAPI schema generation (drf-spectacular)
- URL coverage: all 4 modules' endpoints are reachable
- Django system check
"""
import json
import pytest
from rest_framework import status
from django.test import Client
from django.core.management import call_command
from apps.admissions.models import Enrollment
from apps.finance.models import PaymentLedger
from apps.notifications.models import NotificationLog
from apps.audit.models import AuditLog
from apps.integrations.models import LeadIngestionLog
from tests.factories import (
    SubCenterFactory, StudentFactory, UniversityFactory, CourseFactory,
    IntakeSessionFactory,
)
from tests.base import BaseAPITestCase


@pytest.mark.django_db
class TestEndToEndEnrollmentLifecycle(BaseAPITestCase):
    """
    End-to-end: full student enrollment lifecycle spanning all 4 modules.

    1. Super Admin creates university + course + intake session
    2. Counselor registers student with Aadhar (Module 2)
    3. Counselor uploads documents (Module 2)
    4. Academic Head verifies documents (Module 2)
    5. Counselor creates enrollment (Module 2 + 3 — session enforcement)
    6. Counselor transitions: Applied → Doc Verified → Fee Pending
    7. Razorpay webhook captures payment → Fee Paid (Module 4 + Finance)
    8. WhatsApp notification sent (Module 4)
    """

    def test_full_lifecycle(self):
        # === Step 1: Super Admin sets up catalog ===
        sa_client = self.super_admin_client()
        resp = sa_client.post('/api/v1/universities/', json.dumps({
            'name': 'Mangalayatan University',
            'state': 'Uttar Pradesh',
            'accreditation': 'NAAC A',
        }), content_type='application/json')
        assert resp.status_code == 201
        university_id = resp.data['id']

        resp = sa_client.post('/api/v1/courses/', json.dumps({
            'university': str(university_id),
            'name': 'BCA Online',
            'stream': 'Undergraduate',
            'duration_months': 36,
            'eligibility_text': '12th pass',
        }), content_type='application/json')
        assert resp.status_code == 201
        course_id = resp.data['id']

        resp = sa_client.post('/api/v1/intake-sessions/', json.dumps({
            'session_name': 'October 2026',
            'start_date': '2026-10-01',
            'is_active': True,
            'is_fresh_allowed': True,
        }), content_type='application/json')
        assert resp.status_code == 201
        session_id = resp.data['id']

        # === Step 2: Counselor registers student ===
        coun_client = self.counselor_client(sub_center=self.center_a)
        resp = coun_client.post('/api/v1/students/', json.dumps({
            'full_name': 'Rahul Sharma',
            'dob': '2000-05-15',
            'gender': 'M',
            'primary_phone': '+919876543210',
            'email': 'rahul@example.com',
            'aadhar_number': '123456789012',
            'address_data': {'city': 'Kochi'},
        }), content_type='application/json')
        assert resp.status_code == 201
        student_id = resp.data['id']

        # === Step 3: Document upload ===
        resp = coun_client.post('/api/v1/students-docs/', json.dumps({
            'student': str(student_id),
            'doc_category': 'identity',
            'title': 'Aadhar Card',
            's3_object_uri': 's3://bucket/aadhar.pdf',
        }), content_type='application/json')
        assert resp.status_code == 201
        doc_id = resp.data['id']

        # === Step 4: Academic Head verifies ===
        ah_client = self.academic_head_client()
        resp = ah_client.post(f'/api/v1/students-docs/{doc_id}/verify/')
        assert resp.status_code == 200

        # === Step 5: Create enrollment ===
        resp = coun_client.post('/api/v1/enrollments/', json.dumps({
            'student': str(student_id),
            'course': str(course_id),
            'session': str(session_id),
        }), content_type='application/json')
        assert resp.status_code == 201
        enrollment_id = resp.data['id']

        # === Step 6: Status transitions ===
        # Applied → Document Verified
        resp = coun_client.patch(f'/api/v1/enrollments/{enrollment_id}/status/',
                                 json.dumps({'status': 'Document Verified'}),
                                 content_type='application/json')
        assert resp.status_code == 200

        # Document Verified → Fee Pending
        resp = coun_client.patch(f'/api/v1/enrollments/{enrollment_id}/status/',
                                 json.dumps({'status': 'Fee Pending'}),
                                 content_type='application/json')
        assert resp.status_code == 200

        # === Step 7: Razorpay payment webhook ===
        client = Client()
        webhook_payload = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_e2e_001',
                        'amount': 550000,  # 5500.00 INR in paise
                        'notes': {'enrollment_id': str(enrollment_id)},
                    }
                }
            }
        }
        resp = client.post('/webhooks/razorpay/payments/',
                           data=json.dumps(webhook_payload),
                           content_type='application/json')
        assert resp.status_code == 200

        # Verify enrollment auto-transitioned to Fee Paid
        enrollment = Enrollment.all_objects.get(id=enrollment_id)
        assert enrollment.status == Enrollment.STATUS_FEE_PAID

        # Verify payment ledger created
        ledger = PaymentLedger.all_objects.get(transaction_ref='pay_e2e_001')
        assert float(ledger.amount_paid) == 5500.00

        # === Step 8: Verify WhatsApp notification was sent ===
        notifications = NotificationLog.objects.filter(
            related_enrollment_id=enrollment_id,
            template_id='payment_receipt',
        )
        assert notifications.count() == 1
        assert notifications[0].delivery_status == 'sent'

        # === Verify audit trail exists ===
        audit_entries = AuditLog.objects.filter(action_type='post')
        assert audit_entries.count() >= 3  # university, course, student at minimum


@pytest.mark.django_db
class TestOpenAPISchema:
    """drf-spectacular OpenAPI 3.1 schema generation."""

    def test_schema_generation_succeeds(self):
        from drf_spectacular.generators import SchemaGenerator
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)
        assert 'openapi' in schema
        assert schema['openapi'].startswith('3.')
        assert 'paths' in schema

    def test_all_modules_have_endpoints_in_schema(self):
        from drf_spectacular.generators import SchemaGenerator
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)
        paths = list(schema.get('paths', {}).keys())

        # Module 1: Aggregator
        assert any('/universities' in p for p in paths), 'Missing universities endpoint'
        assert any('/courses' in p for p in paths), 'Missing courses endpoint'

        # Module 2: B2B Portal
        assert any('/students' in p for p in paths), 'Missing students endpoint'
        assert any('/enrollments' in p for p in paths), 'Missing enrollments endpoint'

        # Module 3: Business Logic
        assert any('/intake-sessions' in p for p in paths), 'Missing intake-sessions endpoint'
        assert any('/rules' in p for p in paths), 'Missing rules endpoint'

        # Module 4: Marketing — webhooks are function-based views (not in schema)
        # but notifications endpoints should be present
        assert any('/notifications' in p for p in paths), 'Missing notifications endpoint'

        # Cross-cutting: Finance
        assert any('/payments' in p for p in paths), 'Missing payments endpoint'

        # Sanity: at least 20 endpoints documented
        assert len(paths) >= 20, f'Only {len(paths)} endpoints in schema'

    def test_swagger_ui_accessible(self):
        client = Client()
        resp = client.get('/api/v1/schema/swagger-ui/')
        assert resp.status_code == 200


@pytest.mark.django_db
class TestDjangoSystemCheck:
    """Django's built-in system check passes."""

    def test_system_check_no_issues(self):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        err = StringIO()
        call_command('check', stdout=out, stderr=err)
        assert 'no issues' in out.getvalue().lower()


@pytest.mark.django_db
class TestURLCoverage:
    """Sanity check: all 4 modules have at least one URL registered."""

    def test_all_module_urls_resolvable(self):
        from django.urls import reverse
        # These should all resolve without throwing NoReverseMatch
        reversable = [
            'university-list', 'course-list', 'fee-list', 'prospectus-list',
            'sub-center-list', 'system-user-list', 'student-list',
            'enrollment-list', 'intake-session-list', 'rules-config-list',
            'notification-log-list', 'payment-list',
            'schema', 'swagger-ui', 'redoc',
            'meta-lead-webhook', 'razorpay-webhook',
            'token-auth', 'profile', 'verify-mfa', 'rules-validate', 'broadcast',
        ]
        for name in reversable:
            try:
                url = reverse(name)
                assert url.startswith('/'), f'{name} returned {url}'
            except Exception as e:
                pytest.fail(f'Cannot reverse {name}: {e}')
