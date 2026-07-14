import pytest
pytest.skip('Utility script (not a test) — skipped during pytest collection.', allow_module_level=True)

import traceback
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from apps.admissions.models import Enrollment

user = User.objects.get(username='admin')
# Find an enrollment to transition
enrollment = Enrollment.all_objects.exclude(status='Cancelled').first()
if enrollment:
    print('Found enrollment:', enrollment.id, 'status:', enrollment.status)
    client = APIClient()
    client.force_authenticate(user=user)
    try:
        # Patch the status (it doesn't matter what the new status is as long as it reaches the delay call)
        # We can just try to patch to 'Document Verified' or something if it's 'Applied'
        allowed = enrollment.TRANSITIONS.get(enrollment.status, [])
        if allowed:
            target_status = allowed[0]
            print('Transitioning to:', target_status)
            response = client.patch(f'/api/v1/enrollments/{enrollment.id}/status', {
                'status': target_status
            }, format='json')
            print('STATUS:', response.status_code)
            print('DATA:', response.data)
        else:
            print('No valid transitions')
    except Exception as e:
        traceback.print_exc()
else:
    print('No enrollments found to test.')
