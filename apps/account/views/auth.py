from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from apps.account.forms import UserRegisterForm, ResendVerificationEmailForm
from apps.account.security import is_login_locked, log_security_event, send_verification_email, \
    create_login_attempt, clear_failed_attempts, get_client_ip, get_remaining_lock_minutes
from core.models import User


# login page
# ----------------------------------------------------------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('student')

    form = AuthenticationForm(request, data=request.POST or None)
    form.fields['username'].label = 'Username немесе Email'
    form.fields['username'].widget.attrs.update({
        'placeholder': 'Username немесе email енгізіңіз'
    })

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        ip_address = get_client_ip(request)

        if is_login_locked(username=username, ip_address=ip_address):
            remaining = get_remaining_lock_minutes(username=username, ip_address=ip_address)

            log_security_event(
                event_type='login_failed',
                request=request,
                description=f'Блокталған login әрекеті: {username}',
            )

            messages.error(
                request,
                f'Тым көп қате әрекет жасалды. Қайта көру үшін шамамен {remaining} минут күтіңіз.'
            )
            return render(request, 'app/account/login/page.html', {'form': form})

        if form.is_valid():
            user = form.get_user()

            if not getattr(user, 'email_verified', False):
                create_login_attempt(username=username, request=request, is_successful=False)

                log_security_event(
                    event_type='login_failed',
                    request=request,
                    user=user,
                    description='Email расталмаған аккаунт login жасауға тырысты.',
                )

                messages.error(
                    request,
                    'Алдымен email поштаңызға жіберілген растау сілтемесі арқылы аккаунтыңызды растаңыз.'
                )
                return redirect('resend_verification_email')

            # 2FA қосулы болса — толық login емес, 2FA тексеруге жібереміз
            if getattr(user, 'is_2fa_enabled', False):
                request.session['pre_2fa_user_id'] = user.id
                request.session['pre_2fa_username'] = username

                create_login_attempt(username=username, request=request, is_successful=True)

                messages.info(request, 'Жүйеге кіруді аяқтау үшін Google Authenticator кодын енгізіңіз.')
                return redirect('verify_2fa')

            login(request, user)

            create_login_attempt(username=username, request=request, is_successful=True)
            clear_failed_attempts(username=username, ip_address=ip_address)

            log_security_event(
                event_type='login_success',
                request=request,
                user=user,
                description='Қолданушы жүйеге сәтті кірді.',
            )

            messages.success(request, 'Жүйеге сәтті кірдіңіз.')
            return redirect('student')

        create_login_attempt(username=username, request=request, is_successful=False)

        log_security_event(
            event_type='login_failed',
            request=request,
            description=f'Қате login әрекеті: {username}',
        )

        messages.error(request, 'Логин/email немесе пароль қате.')

    return render(request, 'app/account/login/page.html', {'form': form})


# register page
# ----------------------------------------------------------------------------------------------------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('student')

    form = UserRegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            send_verification_email(request, user)
            log_security_event(
                event_type='register',
                request=request,
                user=user,
                description='Қолданушы тіркелді. Email растау күтілуде.',
            )

            messages.success(
                request,
                'Аккаунт сәтті тіркелді. Email поштаңызға жіберілген растау сілтемесі арқылы аккаунтыңызды белсендіріңіз.'
            )
            return redirect('login')

        messages.error(request, 'Тіркелу кезінде қате шықты. Мәліметтерді қайта тексеріңіз.')
    context = {
        'form': form,
    }
    return render(request, 'app/account/register/page.html', context)


# logout
# ----------------------------------------------------------------------------------------------------------------------
def logout_view(request):
    if request.user.is_authenticated:
        log_security_event(
            event_type='logout',
            request=request,
            user=request.user,
            description='Қолданушы жүйеден шықты.',
        )
    logout(request)
    return redirect('login')



def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None:
        messages.error(request, 'Растау сілтемесі жарамсыз.')
        return redirect('login')

    if user.email_verified:
        messages.info(request, 'Email бұрыннан расталған. Жүйеге кіре аласыз.')
        return redirect('login')

    if not default_token_generator.check_token(user, token):
        messages.error(request, 'Растау сілтемесінің мерзімі өтіп кеткен немесе жарамсыз.')
        return redirect('resend_verification_email')

    user.email_verified = True
    user.save(update_fields=['email_verified'])

    log_security_event(
        event_type='email_verified',
        request=request,
        user=user,
        description='Қолданушы email-ын сәтті растады.',
    )

    messages.success(request, 'Email сәтті расталды. Енді жүйеге кіре аласыз.')
    return redirect('login')


def resend_verification_email_view(request):
    form = ResendVerificationEmailForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email__iexact=email).first()

            if user and not user.email_verified:
                send_verification_email(request, user)

            messages.success(
                request,
                'Егер бұл email жүйеде тіркелген және әлі расталмаған болса, жаңа растау сілтемесі жіберілді.'
            )
            return redirect('login')

        messages.error(request, 'Email енгізуде қате бар.')

    context = {
        'form': form,
    }
    return render(request, 'app/account/verify_email/resend.html', context)
