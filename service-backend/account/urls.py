# service-backend/account/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

app_name = 'account' # Namespace for URLs

urlpatterns = [
    # --- JWT Authentication Endpoints ---
    # Note: These are also defined in core/urls.py. It's common to include them
    # in the app's URLs as well for namespacing, or just use the global ones.
    # We'll define them here for app-specific namespacing.
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # --- Custom Account Management Endpoints ---
    path('register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    # path('password-reset/', views.RequestPasswordResetView.as_view(), name='password_reset_request'),
    # path('password-reset/confirm/', views.ConfirmPasswordResetView.as_view(), name='password_reset_confirm'),
    # path('logout/', views.LogoutView.as_view(), name='logout'), # Optional
]