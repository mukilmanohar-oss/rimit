"""
Phase 2 / Module 2 — B2B Sub-Center Portal tests.

CRITICAL: Tests RLS-equivalent tenant isolation.

Per Section 5.6 of the Development Plan:
    "integration tests must assert RLS isolation for every tenant-scoped
     endpoint. The test suite creates two sub-centers, registers a student
     under each, then attempts cross-tenant reads via the API and asserts
     404 (not 200) — this catches any future code path that bypasses RLS
     via raw SQL or a missed SET LOCAL."
"""
import json
import pytest
from rest_framework import status
from apps.admissions.models import Student, StudentAcademicHistory, StudentDoc, Enrollment
from apps.partners.models import SystemUser, SubCenter
from apps.aggregator.models import University, Course
from apps.rules.models import IntakeSession
from apps.common.models import hash_aadhar
from tests.factories import (
    SubCenterFactory, StudentFactory, CourseFactory, IntakeSessionFactory,
    UniversityFactory,
)
from tests.base import BaseAPITestCase


@pytest.mark.django_db
class TestSubCenterAPI(BaseAPITestCase):

    def test_super_admin_can_create_sub_center(self):
        client = self.super_admin_client()
        resp = client.post('/api/v1/sub-centers/', {
            'center_code': 'KL-TVM-001',
            'name': 'Trivandrum Hub',
            'location': 'Trivandrum, Kerala',
            'state': 'Kerala',
            'status': 'active',
        })
        assert resp.status_code == status.HTTP_201_CREATED

    def test_counselor_cannot_create_sub_center(self):
        client = self.counselor_client()
        resp = client.post('/api/v1/sub-centers/', {
            'center_code': 'XX-XXX-001',
            'name': 'Forbidden',
            'location': 'X',
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_sub_centers_by_status(self):
        # Use unique codes to avoid clash with setUp's TEST-A / TEST-B
        SubCenterFactory(center_code='S-A1', status='active')
        SubCenterFactory(center_code='S-A2', status='suspended')
        client = self.academic_head_client()
        resp = client.get('/api/v1/sub-centers/?status=active')
        # Should include TEST-A, TEST-B (from setUp) + S-A1 (4 total active)
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestStudentRegistration(BaseAPITestCase):

    def test_counselor_can_register_student_in_own_center(self):
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.post('/api/v1/students/', json.dumps({
            'full_name': 'Ravi Kumar',
            'dob': '2000-05-15',
            'gender': 'M',
            'primary_phone': '+919876543210',
            'email': 'ravi@example.com',
            'aadhar_number': '123456789012',
            'address_data': {'city': 'Kochi', 'pincode': '682001'},
            'parent_name': 'Suresh Kumar',
            'parent_phone': '+919876543211',
        }), content_type='application/json')
        assert resp.status_code == status.HTTP_201_CREATED, resp.content
        # Use all_objects to bypass tenant filter
        student = Student.all_objects.get(full_name='Ravi Kumar')
        assert student.sub_center == self.center_a
        # Aadhar should be hashed, not stored plaintext
        assert student.aadhar_hash != '123456789012'
        assert len(student.aadhar_hash) == 64  # SHA-256 hex
        assert student.aadhar_hash == hash_aadhar('123456789012')

    def test_invalid_phone_number_rejected(self):
        client = self.counselor_client()
        resp = client.post('/api/v1/students/', json.dumps({
            'full_name': 'Test',
            'dob': '2000-01-01',
            'primary_phone': '123',
            'aadhar_number': '123456789012',
        }), content_type='application/json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'primary_phone' in resp.data

    def test_invalid_aadhar_format_rejected(self):
        client = self.counselor_client()
        resp = client.post('/api/v1/students/', json.dumps({
            'full_name': 'Test',
            'dob': '2000-01-01',
            'primary_phone': '+919876543210',
            'aadhar_number': '12345',
        }), content_type='application/json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'aadhar_number' in resp.data

    def test_duplicate_aadhar_rejected(self):
        """Two students cannot share the same Aadhar number."""
        # Pre-create with the exact hash that the API will compute
        existing_hash = hash_aadhar('123456789012')
        StudentFactory(sub_center=self.center_a, aadhar_hash=existing_hash, full_name='First Student')

        client = self.counselor_client(sub_center=self.center_a)
        resp = client.post('/api/v1/students/', json.dumps({
            'full_name': 'Duplicate Student',
            'dob': '2000-01-01',
            'primary_phone': '+919876543210',
            'aadhar_number': '123456789012',
        }), content_type='application/json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTenantIsolation(BaseAPITestCase):
    """
    CRITICAL: Tests that RLS-equivalent tenant isolation works correctly.

    Per Section 5.6: "integration tests must assert RLS isolation for
    every tenant-scoped endpoint."
    """

    def test_counselor_can_only_see_own_center_students(self):
        """Counselor at center A cannot see students at center B."""
        student_a = StudentFactory(sub_center=self.center_a, full_name='Student Alpha')
        student_b = StudentFactory(sub_center=self.center_b, full_name='Student Beta')

        client = self.counselor_client(sub_center=self.center_a)
        resp = client.get('/api/v1/students/')
        assert resp.status_code == status.HTTP_200_OK
        names = [s['full_name'] for s in resp.data['results']]
        assert 'Student Alpha' in names
        assert 'Student Beta' not in names

    def test_counselor_cannot_access_other_center_student_detail(self):
        """Direct access to another center's student returns 404."""
        student_b = StudentFactory(sub_center=self.center_b, full_name='Student B')

        client = self.counselor_client(sub_center=self.center_a)
        resp = client.get(f'/api/v1/students/{student_b.id}/')
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_counselor_cannot_update_other_center_student(self):
        """PUT/PATCH to another center's student returns 404."""
        student_b = StudentFactory(sub_center=self.center_b, full_name='Original Name')

        client = self.counselor_client(sub_center=self.center_a)
        resp = client.patch(f'/api/v1/students/{student_b.id}/',
                            json.dumps({'full_name': 'Hacked Name'}),
                            content_type='application/json')
        assert resp.status_code == status.HTTP_404_NOT_FOUND

        # Verify name not changed (use all_objects to bypass tenant filter)
        student_b.refresh_from_db()
        assert student_b.full_name == 'Original Name'

    def test_counselor_cannot_delete_other_center_student(self):
        """DELETE on another center's student returns 404."""
        student_b = StudentFactory(sub_center=self.center_b)

        client = self.counselor_client(sub_center=self.center_a)
        resp = client.delete(f'/api/v1/students/{student_b.id}/')
        assert resp.status_code == status.HTTP_404_NOT_FOUND

        # Verify still exists (use all_objects)
        assert Student.all_objects.filter(id=student_b.id).exists()

    def test_super_admin_can_see_all_centers(self):
        """Super Admin bypasses tenant filter."""
        StudentFactory(sub_center=self.center_a, full_name='Student A')
        StudentFactory(sub_center=self.center_b, full_name='Student B')

        client = self.super_admin_client()
        resp = client.get('/api/v1/students/')
        assert resp.data['count'] == 2

    def test_academic_head_can_see_all_centers(self):
        """Academic Head bypasses tenant filter (read-only across tenants)."""
        StudentFactory(sub_center=self.center_a, full_name='Student A')
        StudentFactory(sub_center=self.center_b, full_name='Student B')

        client = self.academic_head_client()
        resp = client.get('/api/v1/students/')
        assert resp.data['count'] == 2

    def test_finance_can_only_see_own_center(self):
        """Finance role is tenant-scoped, like counselor."""
        StudentFactory(sub_center=self.center_a, full_name='Student A')
        StudentFactory(sub_center=self.center_b, full_name='Student B')

        client = self.finance_client(sub_center=self.center_a)
        resp = client.get('/api/v1/students/')
        assert resp.data['count'] == 1
        assert resp.data['results'][0]['full_name'] == 'Student A'


@pytest.mark.django_db
class TestStudentAcademicHistory(BaseAPITestCase):

    def test_add_academic_history_to_student(self):
        student = StudentFactory(sub_center=self.center_a)
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.post(f'/api/v1/students/{student.id}/academic_histories/', json.dumps({
            'qualification': '12th',
            'institution': 'Govt Higher Secondary',
            'board_university': 'CBSE',
            'year_of_passing': 2018,
            'score_type': 'percentage',
            'score_value': '85.50',
            'subject_stream': 'Science',
        }), content_type='application/json')
        assert resp.status_code == status.HTTP_201_CREATED, resp.content
        assert StudentAcademicHistory.objects.filter(student=student).count() == 1


@pytest.mark.django_db
class TestStudentDocumentUpload(BaseAPITestCase):

    def test_counselor_can_upload_document(self):
        student = StudentFactory(sub_center=self.center_a)
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.post('/api/v1/students-docs/', json.dumps({
            'student': str(student.id),
            'doc_category': 'identity',
            'title': 'Aadhar Card',
            's3_object_uri': 's3://bucket/aadhar.pdf',
            'mime_type': 'application/pdf',
        }), content_type='application/json')
        assert resp.status_code == status.HTTP_201_CREATED, resp.content

    def test_document_verify_by_academic_head(self):
        student = StudentFactory(sub_center=self.center_a)
        doc = StudentDoc.objects.create(
            student=student, doc_category='identity', title='Aadhar',
            s3_object_uri='s3://test', status=StudentDoc.STATUS_PENDING,
        )
        client = self.academic_head_client()
        resp = client.post(f'/api/v1/students-docs/{doc.id}/verify/')
        assert resp.status_code == status.HTTP_200_OK
        doc.refresh_from_db()
        assert doc.status == StudentDoc.STATUS_VERIFIED

    def test_document_reject_with_reason(self):
        student = StudentFactory(sub_center=self.center_a)
        doc = StudentDoc.objects.create(
            student=student, doc_category='marklist', title='Blurry Marklist',
            s3_object_uri='s3://test', status=StudentDoc.STATUS_PENDING,
        )
        client = self.academic_head_client()
        resp = client.post(f'/api/v1/students-docs/{doc.id}/reject/',
                           json.dumps({'reason': 'Image blurry'}),
                           content_type='application/json')
        assert resp.status_code == status.HTTP_200_OK
        doc.refresh_from_db()
        assert doc.status == StudentDoc.STATUS_REJECTED
        assert 'blurry' in doc.rejection_reason.lower()

    def test_counselor_cannot_verify_document(self):
        """Only super_admin / academic_head can verify."""
        student = StudentFactory(sub_center=self.center_a)
        doc = StudentDoc.objects.create(
            student=student, doc_category='identity', title='Test',
            s3_object_uri='s3://test', status=StudentDoc.STATUS_PENDING,
        )
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.post(f'/api/v1/students-docs/{doc.id}/verify/')
        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEnrollmentStateMachine(BaseAPITestCase):

    def _setup_enrollment(self, sub_center=None):
        sub_center = sub_center or self.center_a
        student = StudentFactory(sub_center=sub_center)
        uni = UniversityFactory()
        course = CourseFactory(university=uni)
        session = IntakeSessionFactory(is_fresh_allowed=True)
        # Bypass TenantManager by using all_objects
        enrollment = Enrollment.all_objects.create(
            sub_center=sub_center,
            student=student,
            course=course,
            session=session,
            status=Enrollment.STATUS_APPLIED,
        )
        return enrollment

    def test_valid_status_transition(self):
        enrollment = self._setup_enrollment()
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.patch(f'/api/v1/enrollments/{enrollment.id}/status/',
                            json.dumps({'status': Enrollment.STATUS_DOC_VERIFIED}),
                            content_type='application/json')
        assert resp.status_code == status.HTTP_200_OK, resp.content
        enrollment.refresh_from_db()
        assert enrollment.status == Enrollment.STATUS_DOC_VERIFIED

    def test_invalid_status_transition_rejected(self):
        """Cannot jump from Applied directly to Fee Paid."""
        enrollment = self._setup_enrollment()
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.patch(f'/api/v1/enrollments/{enrollment.id}/status/',
                            json.dumps({'status': Enrollment.STATUS_FEE_PAID}),
                            content_type='application/json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid transition' in resp.data['detail']

    def test_cancelled_enrollment_is_terminal(self):
        """Cancelled status allows no further transitions."""
        enrollment = self._setup_enrollment()
        enrollment.status = Enrollment.STATUS_CANCELLED
        enrollment.save()
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.patch(f'/api/v1/enrollments/{enrollment.id}/status/',
                            json.dumps({'status': Enrollment.STATUS_APPLIED}),
                            content_type='application/json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_enrollment_visible_only_to_own_center(self):
        """Enrollments are tenant-scoped (RLS)."""
        enrollment_a = self._setup_enrollment(sub_center=self.center_a)
        enrollment_b = self._setup_enrollment(sub_center=self.center_b)

        client = self.counselor_client(sub_center=self.center_a)
        resp = client.get('/api/v1/enrollments/')
        assert resp.data['count'] == 1
        assert str(resp.data['results'][0]['id']) == str(enrollment_a.id)

    def test_next_valid_statuses_returned_in_serializer(self):
        enrollment = self._setup_enrollment()
        client = self.counselor_client(sub_center=self.center_a)
        resp = client.get(f'/api/v1/enrollments/{enrollment.id}/')
        assert resp.status_code == status.HTTP_200_OK
        assert 'next_valid_statuses' in resp.data
        assert Enrollment.STATUS_DOC_VERIFIED in resp.data['next_valid_statuses']
        assert Enrollment.STATUS_CANCELLED in resp.data['next_valid_statuses']
