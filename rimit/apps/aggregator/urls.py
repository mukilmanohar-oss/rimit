"""URL routes for aggregator app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.aggregator.views import (
    UniversityViewSet, CourseViewSet, FeeStructureViewSet, UniversityDocVaultViewSet,
)

router = DefaultRouter()
router.register('universities', UniversityViewSet, basename='university')
router.register('courses', CourseViewSet, basename='course')
router.register('fees', FeeStructureViewSet, basename='fee')
router.register('prospectus', UniversityDocVaultViewSet, basename='prospectus')

urlpatterns = [
    path('', include(router.urls)),
]
