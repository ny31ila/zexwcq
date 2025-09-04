# service-backend/core/urls.py
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # JWT Authentication endpoints (Global, as in previous version)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Captcha URLs
    path('captcha/', include('captcha.urls')),
    # Include app URLs
    # Note: The account app also defines its own JWT URLs. Both can co-exist.
    # Using namespaced includes is good practice.
    path('api/account/', include('account.urls', namespace='account')),
    # Add paths for other apps as they are developed and tested
    path('api/assessment/', include('assessment.urls', namespace='assessment')),
    path('api/ai/', include('ai_integration.urls', namespace='ai_integration')),
    path('api/resume/', include('resume.urls', namespace='resume')),
    path('api/skill/', include('skill.urls', namespace='skill')),
    path('api/career/', include('career.urls', namespace='career')),
    path('api/counseling/', include('counseling.urls', namespace='counseling')),
    path('api/content/', include('content.urls', namespace='content')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Note: In production, serve static files with a web server like Nginx, not Django.
