from django.urls import path
from .views import auth, account, password_reset, passkeys


urlpatterns = [
    # base auth
    path('login/', auth.login_view, name='login'),
    path('register/', auth.register_view, name='register'),
    path('logout/', auth.logout_view, name='logout'),

    path('forgot-password/', password_reset.SecurePasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', password_reset.SecurePasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', password_reset.SecurePasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/complete/', password_reset.SecurePasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # verify email
    path('verify-email/<uidb64>/<token>/', auth.verify_email_view, name='verify_email'),
    path('resend-verification-email/', auth.resend_verification_email_view, name='resend_verification_email'),

    # m2a
    path('verify-2fa/', account.verify_2fa_view, name='verify_2fa'),

    # face ID
    path('passkeys/register/begin/', passkeys.begin_passkey_registration_view, name='begin_passkey_registration'),
    path('passkeys/register/finish/', passkeys.finish_passkey_registration_view, name='finish_passkey_registration'),
    path('passkeys/auth/begin/', passkeys.begin_passkey_authentication_view, name='begin_passkey_authentication'),
    path('passkeys/auth/finish/', passkeys.finish_passkey_authentication_view, name='finish_passkey_authentication'),

    # account settings
    path('user/me/', account.account_view, name='account'),
    path('user/settings/', account.settings_view, name='settings'),

    path('user/settings/2fa/setup/', account.setup_2fa_view, name='setup_2fa'),
    path('user/settings/2fa/disable/', account.settings_view, name='disable_2fa'),
    path('user/settings/2fa/backup-codes/', account.two_factor_backup_codes_view, name='two_factor_backup_codes'),

    path('user/settings/passkeys/<int:pk>/remove/', passkeys.remove_passkey_view, name='remove_passkey'),

]