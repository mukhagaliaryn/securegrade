from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from apps.account.forms import (
    UserUpdateForm,
    DeleteAccountForm,
    TwoFactorVerifyForm,
    TwoFactorDisableForm,
    TwoFactorSetupForm,
)
from apps.account.security import (
    build_totp_uri,
    generate_backup_codes,
    generate_qr_code_base64,
    generate_totp_secret,
    log_security_event,
    verify_totp_code,
)
from core.models import User


@login_required
def account_view(request):
    user = request.user

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            log_security_event(
                event_type='profile_updated',
                request=request,
                user=user,
                description='Профиль мәліметтері жаңартылды.',
            )
            messages.success(request, _('Профиль сәтті жаңартылды'))
            return redirect('account')
    else:
        form = UserUpdateForm(instance=user)

    context = {'form': form}
    return render(request, 'app/account/user/me/page.html', context)


@login_required
def settings_view(request):
    user = request.user

    password_form = PasswordChangeForm(user=user)
    delete_form = DeleteAccountForm(user=user)
    disable_2fa_form = TwoFactorDisableForm(user=user)

    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)

                log_security_event(
                    event_type='password_changed',
                    request=request,
                    user=user,
                    description='Құпиясөз сәтті өзгертілді.',
                )

                messages.success(request, _('Құпиясөз сәтті өзгертілді'))
                return redirect('settings')
            messages.error(request, _('Қате! Құпиясөз өзгертілмеді'))

        elif 'delete_account' in request.POST:
            delete_form = DeleteAccountForm(request.POST, user=user)
            if delete_form.is_valid():
                log_security_event(
                    event_type='account_deleted',
                    request=request,
                    user=user,
                    description='Қолданушы аккаунтын жойды.',
                )
                user.delete()
                messages.success(request, _('Аккаунт жойылды'))
                return redirect('login')
            messages.error(request, _('Аккаунтты жою үшін парольді дұрыс растаңыз.'))

        elif 'disable_2fa' in request.POST:
            disable_2fa_form = TwoFactorDisableForm(request.POST, user=user)
            if disable_2fa_form.is_valid():
                user.is_2fa_enabled = False
                user.otp_secret = ''
                user.backup_codes = []
                user.save(update_fields=['is_2fa_enabled', 'otp_secret', 'backup_codes'])

                log_security_event(
                    event_type='2fa_disabled',
                    request=request,
                    user=user,
                    description='Қолданушы 2FA-ны өшірді.',
                )

                messages.success(request, 'Екі факторлы қорғаныс өшірілді.')
                return redirect('settings')

            messages.error(request, '2FA-ны өшіру үшін пароль қате.')

    context = {
        'password_form': password_form,
        'delete_form': delete_form,
        'disable_2fa_form': disable_2fa_form,
    }
    return render(request, 'app/account/user/settings/page.html', context)


@login_required
def setup_2fa_view(request):
    user = request.user

    if user.is_2fa_enabled:
        messages.info(request, '2FA бұрыннан қосулы.')
        return redirect('settings')

    secret = request.session.get('pending_2fa_secret')
    if not secret:
        secret = generate_totp_secret()
        request.session['pending_2fa_secret'] = secret

    form = TwoFactorSetupForm(request.POST or None)

    uri = build_totp_uri(user, secret)
    qr_code = generate_qr_code_base64(uri)

    if request.method == 'POST':
        if form.is_valid():
            code = form.cleaned_data['code']

            if verify_totp_code(secret, code):
                backup_codes = generate_backup_codes()

                user.otp_secret = secret
                user.is_2fa_enabled = True
                user.backup_codes = backup_codes
                user.save(update_fields=['otp_secret', 'is_2fa_enabled', 'backup_codes'])

                request.session.pop('pending_2fa_secret', None)
                request.session['fresh_backup_codes'] = backup_codes

                log_security_event(
                    event_type='2fa_enabled',
                    request=request,
                    user=user,
                    description='Қолданушы 2FA-ны қосты.',
                )

                messages.success(request, 'Екі факторлы қорғаныс сәтті қосылды.')
                return redirect('two_factor_backup_codes')

            messages.error(request, 'Authenticator коды қате.')

    context = {
        'form': form,
        'secret': secret,
        'qr_code': qr_code,
    }
    return render(request, 'app/account/user/settings/2fa_setup.html', context)


@login_required
def two_factor_backup_codes_view(request):
    codes = request.session.get('fresh_backup_codes')
    if not codes:
        messages.info(request, 'Жаңа backup кодтар табылмады.')
        return redirect('settings')

    return render(
        request,
        'app/account/user/settings/2fa_backup_codes.html',
        {'codes': codes}
    )


def verify_2fa_view(request):
    pre_2fa_user_id = request.session.get('pre_2fa_user_id')
    pre_2fa_username = request.session.get('pre_2fa_username', '')

    if not pre_2fa_user_id:
        messages.error(request, '2FA сессиясы табылмады. Қайта кіріп көріңіз.')
        return redirect('login')

    try:
        user = User.objects.get(id=pre_2fa_user_id)
    except User.DoesNotExist:
        request.session.pop('pre_2fa_user_id', None)
        request.session.pop('pre_2fa_username', None)
        messages.error(request, 'Қолданушы табылмады.')
        return redirect('login')

    form = TwoFactorVerifyForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            code = form.cleaned_data['code'].strip().upper()

            # TOTP код
            if verify_totp_code(user.otp_secret, code):
                login(request, user, backend='core.utils.backends.EmailOrUsernameModelBackend')
                request.session.pop('pre_2fa_user_id', None)
                request.session.pop('pre_2fa_username', None)

                log_security_event(
                    event_type='2fa_challenge_passed',
                    request=request,
                    user=user,
                    description='2FA коды дұрыс енгізілді.',
                )
                log_security_event(
                    event_type='login_success',
                    request=request,
                    user=user,
                    description='Қолданушы 2FA арқылы жүйеге сәтті кірді.',
                )

                messages.success(request, '2FA тексеруі сәтті өтті.')
                return redirect('student')

            # Backup code
            if code in [item.upper() for item in user.backup_codes]:
                updated_codes = [item for item in user.backup_codes if item.upper() != code]
                user.backup_codes = updated_codes
                user.save(update_fields=['backup_codes'])

                login(request, user)
                request.session.pop('pre_2fa_user_id', None)
                request.session.pop('pre_2fa_username', None)

                log_security_event(
                    event_type='2fa_backup_code_used',
                    request=request,
                    user=user,
                    description='Қосалқы код қолданылды.',
                )
                log_security_event(
                    event_type='2fa_challenge_passed',
                    request=request,
                    user=user,
                    description='2FA backup code арқылы өтті.',
                )

                messages.success(request, 'Қосалқы код арқылы сәтті кірдіңіз.')
                return redirect('student')

            log_security_event(
                event_type='2fa_challenge_failed',
                request=request,
                user=user,
                description=f'Қате 2FA әрекеті: {pre_2fa_username}',
            )
            messages.error(request, '2FA коды немесе backup code қате.')

    return render(request, 'app/account/verify_2fa/page.html', {'form': form})