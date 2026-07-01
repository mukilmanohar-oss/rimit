"""URL routes for notifications app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.notifications.views import NotificationLogViewSet, BroadcastView

router = DefaultRouter(trailing_slash=False)
router.register('notifications/logs', NotificationLogViewSet, basename='notification-log')

urlpatterns = [
    path('', include(router.urls)),
    path('notifications/broadcast/', BroadcastView.as_view(), name='broadcast'),
]
