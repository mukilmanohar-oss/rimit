"""URL routes for rules app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.rules.views import (
    IntakeSessionViewSet, RulesConfigurationViewSet, EnrollmentValidationView,
)

router = DefaultRouter(trailing_slash=False)
router.register('intake-sessions', IntakeSessionViewSet, basename='intake-session')
router.register('rules/session-matrix', RulesConfigurationViewSet, basename='rules-config')

urlpatterns = [
    path('', include(router.urls)),
    path('rules/validate', EnrollmentValidationView.as_view(), name='rules-validate'),
]
