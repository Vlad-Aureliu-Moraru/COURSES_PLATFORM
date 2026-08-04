from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    SignupResendView,
    SignupVerifyView,
    SignupView,
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='auth-signup'),
    path('signup/verify/', SignupVerifyView.as_view(), name='auth-signup-verify'),
    path('signup/resend/', SignupResendView.as_view(), name='auth-signup-resend'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('profile/', ProfileView.as_view(), name='auth-profile'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='auth-password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
]
