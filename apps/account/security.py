from datetime import timedelta
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from core.models import LoginAttempt, SecurityEvent


DEFAULT_MAX_FAILED_LOGIN_ATTEMPTS = 5
DEFAULT_FAILED_LOGIN_WINDOW_MINUTES = 15
DEFAULT_LOGIN_LOCKOUT_MINUTES = 15


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')[:1000]


def get_login_limits():
    return {
        'max_attempts': getattr(settings, 'MAX_FAILED_LOGIN_ATTEMPTS', DEFAULT_MAX_FAILED_LOGIN_ATTEMPTS),
        'window_minutes': getattr(settings, 'FAILED_LOGIN_WINDOW_MINUTES', DEFAULT_FAILED_LOGIN_WINDOW_MINUTES),
        'lockout_minutes': getattr(settings, 'LOGIN_LOCKOUT_MINUTES', DEFAULT_LOGIN_LOCKOUT_MINUTES),
    }


def record_login_attempt(*, request, username, is_successful):
    return LoginAttempt.objects.create(
        username=(username or '')[:150],
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        is_successful=is_successful,
    )


def log_security_event(*, event_type, request, user=None, description=''):
    return SecurityEvent.objects.create(
        user=user,
        event_type=event_type,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        description=description,
    )


def get_recent_failed_attempts(*, username, request):
    limits = get_login_limits()
    threshold = timezone.now() - timedelta(minutes=limits['window_minutes'])
    ip_address = get_client_ip(request)
    return LoginAttempt.objects.filter(
        created_at__gte=threshold,
        is_successful=False,
        username=(username or '')[:150],
        ip_address=ip_address,
    )


def is_login_locked(*, username, request):
    limits = get_login_limits()
    failures = get_recent_failed_attempts(username=username, request=request)
    if failures.count() < limits['max_attempts']:
        return False, None

    latest_failure = failures.order_by('-created_at').first()
    if latest_failure is None:
        return False, None

    locked_until = latest_failure.created_at + timedelta(minutes=limits['lockout_minutes'])
    if timezone.now() >= locked_until:
        return False, None
    return True, locked_until


def log_security_event(event_type, request=None, user=None, description=''):
    ip_address = get_client_ip(request) if request else None
    user_agent = get_user_agent(request) if request else ''

    return SecurityEvent.objects.create(
        user=user,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        description=description or '',
    )


def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    verify_path = reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    verify_url = request.build_absolute_uri(verify_path)

    context = {
        'user': user,
        'verify_url': verify_url,
        'site_name': 'SecureGrade',
    }

    subject = render_to_string(
        'app/account/emails/verify_email_subject.txt',
        context
    ).strip()

    text_body = render_to_string(
        'app/account/emails/verify_email_email.txt',
        context
    )

    html_body = render_to_string(
        'app/account/emails/verify_email_email.html',
        context
    )
    send_mail(
        subject=subject,
        message=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_body,
        fail_silently=False,
    )
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=['email_verification_sent_at'])

    log_security_event(
        event_type='email_verification_sent',
        request=request,
        user=user,
        description='Email verification сілтемесі жіберілді.',
    )


def is_login_locked(username: str, ip_address: str) -> bool:
    if not username:
        return False

    window_minutes = getattr(settings, 'FAILED_LOGIN_WINDOW_MINUTES', 15)
    max_attempts = getattr(settings, 'MAX_FAILED_LOGIN_ATTEMPTS', 5)

    window_start = timezone.now() - timedelta(minutes=window_minutes)

    failed_attempts = LoginAttempt.objects.filter(
        username__iexact=username,
        ip_address=ip_address,
        is_successful=False,
        created_at__gte=window_start,
    ).count()

    return failed_attempts >= max_attempts


def get_remaining_lock_minutes(username: str, ip_address: str) -> int:
    """
    Шамамен қанша минут күту керек екенін қайтарады.
    """
    if not username:
        return 0

    window_minutes = getattr(settings, 'FAILED_LOGIN_WINDOW_MINUTES', 15)

    last_failed = LoginAttempt.objects.filter(
        username__iexact=username,
        ip_address=ip_address,
        is_successful=False,
    ).order_by('-created_at').first()

    if not last_failed:
        return 0

    unlock_time = last_failed.created_at + timedelta(minutes=window_minutes)
    remaining = unlock_time - timezone.now()

    if remaining.total_seconds() <= 0:
        return 0

    minutes = int(remaining.total_seconds() // 60)
    return max(minutes, 1)


def create_login_attempt(username: str, request, is_successful: bool):
    return LoginAttempt.objects.create(
        username=(username or '').strip(),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        is_successful=is_successful,
    )


def clear_failed_attempts(username: str, ip_address: str):
    """
    Сәтті login болғанда осы username/ip бойынша recent failed attempt-терді тазалауға болады.
    Міндетті емес, бірақ UX жақсырақ болады.
    """
    if not username:
        return

    LoginAttempt.objects.filter(
        username__iexact=username,
        ip_address=ip_address,
        is_successful=False,
    ).delete()
