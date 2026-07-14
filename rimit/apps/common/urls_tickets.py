
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.common.views_tickets import TicketViewSet

router = DefaultRouter(trailing_slash=False)
router.register('tickets', TicketViewSet, basename='ticket')

urlpatterns = [
    path('', include(router.urls)),
]
