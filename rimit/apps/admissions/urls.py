"""URL routes for admissions app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.admissions.views import (
    StudentViewSet, StudentAcademicHistoryViewSet, StudentDocViewSet, EnrollmentViewSet,
)

router = DefaultRouter()
router.register('students', StudentViewSet, basename='student')
router.register('academic-histories', StudentAcademicHistoryViewSet, basename='academic-history')
router.register('students-docs', StudentDocViewSet, basename='student-doc')
router.register('enrollments', EnrollmentViewSet, basename='enrollment')

urlpatterns = [
    path('', include(router.urls)),
]
