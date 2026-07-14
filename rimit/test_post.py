import pytest
pytest.skip('Utility script (not a test) — skipped during pytest collection.', allow_module_level=True)

import traceback
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from apps.admissions.models import Student
from apps.aggregator.models import Course
from apps.rules.models import IntakeSession

user = User.objects.get(username='admin')
student = Student.all_objects.first()
course = Course.objects.first()
session = IntakeSession.objects.first()

client = APIClient()
client.force_authenticate(user=user)

try:
    response = client.post('/api/v1/enrollments', {
        'student': student.id,
        'course': course.id,
        'session': session.id,
        'status': 'Applied'
    }, format='json')
    print('STATUS:', response.status_code)
    print('DATA:', response.data)
except Exception as e:
    traceback.print_exc()
