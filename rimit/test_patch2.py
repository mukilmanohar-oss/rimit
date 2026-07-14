import pytest
pytest.skip('Utility script (not a test) — skipped during pytest collection.', allow_module_level=True)

import traceback
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from apps.admissions.models import Enrollment

user = User.objects.get(username='admin')
enrollment = Enrollment.all_objects.exclude(status='Cancelled').first()
if enrollment:
    client = APIClient()
    client.force_authenticate(user=user)
    try:
        allowed = enrollment.TRANSITIONS.get(enrollment.status, [])
        if allowed:
            target_status = allowed[0]
            # Try invalid target if possible, or just re-try Fee Paid if Fee Pending
            response = client.patch(f'/api/v1/enrollments/{enrollment.id}/status', {
                'status': 'Fee Paid'
            }, format='json')
            print('STATUS:', response.status_code)
            print('DATA:', response.data)
    except Exception as e:
        traceback.print_exc()
