"""URL routes for integrations API (authenticated, read-only monitoring)."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.integrations.views_api import LeadIngestionLogViewSet

router = DefaultRouter(trailing_slash=False)
router.register('lead-ingestion-logs', LeadIngestionLogViewSet, basename='lead-ingestion-log')

urlpatterns = [
    path('', include(router.urls)),
]
