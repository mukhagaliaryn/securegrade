from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from apps.account.forms import DeleteAccountForm, UserUpdateForm
from apps.account.security import log_security_event


# account page
# ----------------------------------------------------------------------------------------------------------------------
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
                description=_('Пайдаланушы профиль деректерін жаңартты.'),
            )
            messages.success(request, _('Профиль сәтті жаңартылды'))
            return redirect('account')
    else:
        form = UserUpdateForm(instance=user)

    context = {'form': form}
    return render(request, 'app/account/user/me/page.html', context)


# settings page
# ----------------------------------------------------------------------------------------------------------------------
@login_required
def settings_view(request):
    user = request.user
    password_form = PasswordChangeForm(user=user)
    delete_form = DeleteAccountForm(user=user)

    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=user, data=request.POST)
            delete_form = DeleteAccountForm(user=user)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                log_security_event(
                    event_type='password_changed',
                    request=request,
                    user=user,
                    description=_('Пайдаланушы құпиясөзін өзгертті.'),
                )
                messages.success(request, _('Құпиясөз сәтті өзгертілді'))
                return redirect('settings')
            else:
                messages.error(request, _('Қате! Құпиясөз өзгертілмеді'))

        elif 'delete_account' in request.POST:
            delete_form = DeleteAccountForm(request.POST, user=user)
            password_form = PasswordChangeForm(user=user)
            if delete_form.is_valid():
                log_security_event(
                    event_type='account_deleted',
                    request=request,
                    user=user,
                    description=_('Пайдаланушы өз аккаунтын жойды.'),
                )
                request.user.delete()
                messages.success(request, _('Аккаунт жойылды'))
                return redirect('login')
            messages.error(request, _('Аккаунтты жою үшін растауды толық толтырыңыз.'))

    context = {
        'password_form': password_form,
        'delete_form': delete_form,
    }
    return render(request, 'app/account/user/settings/page.html', context)
