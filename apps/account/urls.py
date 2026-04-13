from django.urls import path
from .views import auth, account, password_reset


urlpatterns = [
    # auth urls...
    path('login/', auth.login_view, name='login'),
    path('register/', auth.register_view, name='register'),
    path('logout/', auth.logout_view, name='logout'),

    # verify
    path('verify-email/<uidb64>/<token>/', auth.verify_email_view, name='verify_email'),
    path('resend-verification-email/', auth.resend_verification_email_view, name='resend_verification_email'),

    # password reset
    path('forgot-password/', password_reset.SecurePasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', password_reset.SecurePasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', password_reset.SecurePasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/complete/', password_reset.SecurePasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # user urls...
    path('user/me/', account.account_view, name='account'),
    path('user/settings/', account.settings_view, name='settings'),
]
