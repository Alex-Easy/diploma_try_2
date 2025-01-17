from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Swagger/Redoc for API documentation
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Base URL patterns
urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls, name='admin-panel'),
    path('baton/', include('baton.urls')),

    # Application-specific URLs
    path('api/v1/', include('procurement.urls'), name='api-root'),

    # API documentation endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug Toolbar (only in DEBUG mode)
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls), name='debug-toolbar'),
        ] + urlpatterns
    except ImportError:
        pass  # If debug_toolbar is not installed, skip adding debug routes
