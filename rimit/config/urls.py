"""URL configuration for RIMIT B2B Aggregator."""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/', include([
        path('', include('apps.aggregator.urls')),
        path('', include('apps.partners.urls')),
        path('', include('apps.admissions.urls')),
        path('', include('apps.rules.urls')),
        path('', include('apps.finance.urls')),
        path('', include('apps.notifications.urls')),
        path('', include('apps.integrations.urls')),
        path('auth/', include('apps.common.urls_auth')),
        path('support/', include('apps.common.urls_tickets')),
    ])),

    # Webhooks (no JWT auth, HMAC verified in view)
    path('webhooks/', include([
        path('', include('apps.integrations.urls_webhooks')),
    ])),

    # OpenAPI schema
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

from django.conf import settings
from django.conf.urls.static import static

if getattr(settings, 'USE_LOCAL_STORAGE', True):
    urlpatterns += static(settings.MEDIA_URL, document_root=getattr(settings, 'LOCAL_STORAGE_PATH', settings.MEDIA_ROOT))
