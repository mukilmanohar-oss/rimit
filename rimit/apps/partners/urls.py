"""URL routes for partners app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.partners.views import SubCenterViewSet, SystemUserViewSet, SubCenterUniversityMappingViewSet

router = DefaultRouter(trailing_slash=False)
router.register('sub-centers', SubCenterViewSet, basename='sub-center')
router.register('users', SystemUserViewSet, basename='system-user')
router.register('sub-center-university-mappings', SubCenterUniversityMappingViewSet, basename='sub-center-university-mapping')

urlpatterns = [
    path('', include(router.urls)),
]
