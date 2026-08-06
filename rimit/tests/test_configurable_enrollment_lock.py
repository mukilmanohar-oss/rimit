import pytest
from rest_framework import status
from django.test import override_settings
from apps.admissions.models import Enrollment
from tests.base import BaseAPITestCase
from tests.factories import EnrollmentFactory

@pytest.mark.django_db
class TestConfigurableEnrollmentLock(BaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.client = self.super_admin_client()

    @override_settings(RESTRICT_EDIT_ENROLLMENT_STATUS='Enrolled')
    def test_edit_before_lock_status_succeeds(self):
        # Applied is before Enrolled, so update should succeed
        enrollment = EnrollmentFactory(sub_center=self.center_a, status='Applied')
        resp = self.client.patch(
            f'/api/v1/enrollments/{enrollment.id}',
            {'notes': 'Updated notes text'},
            format='json'
        )
        assert resp.status_code == status.HTTP_200_OK, resp.content
        enrollment.refresh_from_db()
        assert enrollment.notes == 'Updated notes text'

    @override_settings(RESTRICT_EDIT_ENROLLMENT_STATUS='Enrolled')
    def test_edit_at_lock_status_fails(self):
        # Enrolled is the lock status, so update should fail
        enrollment = EnrollmentFactory(sub_center=self.center_a, status='Enrolled')
        resp = self.client.patch(
            f'/api/v1/enrollments/{enrollment.id}',
            {'notes': 'Updated notes text'},
            format='json'
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.content
        assert "Updates are not allowed once enrollment has reached status" in str(resp.content)

    @override_settings(RESTRICT_EDIT_ENROLLMENT_STATUS='Enrolled')
    def test_edit_after_lock_status_fails(self):
        # Enrollment Generated is after Enrolled, so update should fail
        enrollment = EnrollmentFactory(sub_center=self.center_a, status='Enrollment Generated')
        resp = self.client.patch(
            f'/api/v1/enrollments/{enrollment.id}',
            {'notes': 'Updated notes text'},
            format='json'
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.content
        assert "Updates are not allowed once enrollment has reached status" in str(resp.content)

    @override_settings(RESTRICT_EDIT_ENROLLMENT_STATUS='Fee Pending')
    def test_custom_lock_status_enforced(self):
        # If lock status is Fee Pending:
        # Applied: can edit
        enrollment_applied = EnrollmentFactory(sub_center=self.center_a, status='Applied')
        resp_applied = self.client.patch(
            f'/api/v1/enrollments/{enrollment_applied.id}',
            {'notes': 'OK'},
            format='json'
        )
        assert resp_applied.status_code == status.HTTP_200_OK

        # Fee Pending: cannot edit
        enrollment_pending = EnrollmentFactory(sub_center=self.center_a, status='Fee Pending')
        resp_pending = self.client.patch(
            f'/api/v1/enrollments/{enrollment_pending.id}',
            {'notes': 'Block me'},
            format='json'
        )
        assert resp_pending.status_code == status.HTTP_400_BAD_REQUEST

    @override_settings(RESTRICT_EDIT_ENROLLMENT_STATUS='Enrolled')
    def test_cancelled_enrollment_always_blocked(self):
        # Cancelled is always blocked, regardless of settings
        enrollment = EnrollmentFactory(sub_center=self.center_a, status='Cancelled')
        resp = self.client.patch(
            f'/api/v1/enrollments/{enrollment.id}',
            {'notes': 'Should fail'},
            format='json'
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.content
        assert "Updates are not allowed for Cancelled enrollments." in str(resp.content)

    @override_settings(RESTRICT_EDIT_ENROLLMENT_STATUS='InvalidStatusValue')
    def test_invalid_lock_status_falls_back_to_enrolled(self):
        # Enrolled should be used as fallback when lock status is invalid.
        # Edits at Enrolled should fail.
        enrollment = EnrollmentFactory(sub_center=self.center_a, status='Enrolled')
        resp = self.client.patch(
            f'/api/v1/enrollments/{enrollment.id}',
            {'notes': 'Should block'},
            format='json'
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Updates are not allowed once enrollment has reached status 'Enrolled'" in resp.content.decode('utf-8')

        # Edits before Enrolled (e.g. Applied) should succeed.
        enrollment_applied = EnrollmentFactory(sub_center=self.center_a, status='Applied')
        resp_applied = self.client.patch(
            f'/api/v1/enrollments/{enrollment_applied.id}',
            {'notes': 'Should succeed'},
            format='json'
        )
        assert resp_applied.status_code == status.HTTP_200_OK

