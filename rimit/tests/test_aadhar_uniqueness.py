"""
test_aadhar_uniqueness.py

Tests that enforce the required + unique Aadhar number constraint
end-to-end through the API.

These tests use fresh factory data and do NOT read from or alter
any pre-existing DB rows.
"""
from tests.base import BaseAPITestCase
from tests.factories import CourseFactory, SubCenterFactory, StudentFactory


class TestDuplicateAadharRejection(BaseAPITestCase):
    """Duplicate Aadhar via API must return 400 with a clear message — never 201/500."""

    def setUp(self):
        super().setUp()
        self.client = self.super_admin_client()
        self.course = CourseFactory()

    def _student_payload(self, aadhar, phone='9876540001', name='Test Student A'):
        return {
            'full_name': name,
            'dob': '2000-06-15',
            'gender': 'M',
            'primary_phone': phone,
            'email': f'{phone}@test.com',
            'aadhar_number': aadhar,
            'course': str(self.course.id),
        }

    def test_first_registration_succeeds(self):
        """Baseline: a unique Aadhar is accepted with 201."""
        resp = self.client.post('/api/v1/students', self._student_payload('444455556666'), format='json')
        self.assertEqual(resp.status_code, 201, msg=resp.data)

    def test_duplicate_aadhar_returns_400(self):
        """Submitting the same Aadhar number twice must return 400, not 201 or 500."""
        aadhar = '777788889999'
        # First submission — must succeed
        resp1 = self.client.post('/api/v1/students', self._student_payload(aadhar, phone='9876540002'), format='json')
        self.assertEqual(resp1.status_code, 201, msg=f'First registration failed unexpectedly: {resp1.data}')

        # Second submission — same Aadhar, different person
        resp2 = self.client.post(
            '/api/v1/students',
            self._student_payload(aadhar, phone='9876540003', name='Test Student B'),
            format='json',
        )
        self.assertEqual(resp2.status_code, 400,
                         msg=f'Duplicate Aadhar was accepted (status={resp2.status_code}): {resp2.data}')

    def test_duplicate_rejection_contains_specific_message(self):
        """The 400 response must identify aadhar_number and contain the canonical message."""
        aadhar = '111100002222'
        self.client.post('/api/v1/students', self._student_payload(aadhar, phone='9876540004'), format='json')

        resp = self.client.post(
            '/api/v1/students',
            self._student_payload(aadhar, phone='9876540005', name='Test Student C'),
            format='json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('aadhar_number', resp.data,
                      msg=f'Expected aadhar_number field in error, got: {resp.data}')
        error_msg = resp.data['aadhar_number']
        if isinstance(error_msg, list):
            error_msg = error_msg[0]
        self.assertIn('already exists', str(error_msg),
                      msg=f"Expected 'already exists' in message, got: {error_msg}")

    def test_duplicate_check_endpoint_returns_exists_true(self):
        """GET /students/check-aadhar must return exists=True for a registered Aadhar."""
        aadhar = '333344445555'
        self.client.post('/api/v1/students', self._student_payload(aadhar, phone='9876540006'), format='json')

        resp = self.client.get('/api/v1/students/check-aadhar', {'aadhar': aadhar})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data.get('exists'), msg=f'Expected exists=True, got: {resp.data}')

    def test_duplicate_check_endpoint_returns_exists_false_for_new_aadhar(self):
        """GET /students/check-aadhar must return exists=False for an unregistered Aadhar."""
        resp = self.client.get('/api/v1/students/check-aadhar', {'aadhar': '000011112222'})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data.get('exists'), msg=f'Expected exists=False, got: {resp.data}')


class TestAadharRequired(BaseAPITestCase):
    """Blank or missing aadhar_number must be rejected at the serializer level."""

    def setUp(self):
        super().setUp()
        self.client = self.super_admin_client()
        self.course = CourseFactory()

    def _base_payload(self):
        return {
            'full_name': 'No Aadhar Student',
            'dob': '1995-03-20',
            'gender': 'F',
            'primary_phone': '9876540099',
            'email': 'noaadhar@test.com',
            'course': str(self.course.id),
        }

    def test_missing_aadhar_returns_400(self):
        """A payload without aadhar_number must be rejected with 400."""
        payload = self._base_payload()
        # aadhar_number intentionally omitted
        resp = self.client.post('/api/v1/students', payload, format='json')
        self.assertEqual(resp.status_code, 400,
                         msg=f'Expected 400 for missing aadhar, got {resp.status_code}: {resp.data}')
        self.assertIn('aadhar_number', resp.data,
                      msg=f'Expected aadhar_number in error, got: {resp.data}')

    def test_blank_aadhar_returns_400(self):
        """A payload with empty aadhar_number must be rejected with 400."""
        payload = {**self._base_payload(), 'aadhar_number': ''}
        resp = self.client.post('/api/v1/students', payload, format='json')
        self.assertEqual(resp.status_code, 400,
                         msg=f'Expected 400 for blank aadhar, got {resp.status_code}: {resp.data}')
        self.assertIn('aadhar_number', resp.data,
                      msg=f'Expected aadhar_number in error, got: {resp.data}')

    def test_invalid_format_aadhar_returns_400(self):
        """A non-12-digit Aadhar must be rejected with 400."""
        payload = {**self._base_payload(), 'aadhar_number': '12345'}
        resp = self.client.post('/api/v1/students', payload, format='json')
        self.assertEqual(resp.status_code, 400,
                         msg=f'Expected 400 for invalid aadhar, got {resp.status_code}: {resp.data}')
        self.assertIn('aadhar_number', resp.data,
                      msg=f'Expected aadhar_number in error, got: {resp.data}')
