import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.account.security import log_security_event
from apps.account.webauthn_utils import (
    build_exclude_credentials,
    get_authentication_options,
    get_registration_options_for_user,
    verify_authentication_credential,
    verify_registration_credential, bytes_to_base64url,
)
from core.models import PasskeyCredential


def _json_body(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


@login_required
@require_POST
def begin_passkey_registration_view(request):
    user = request.user
    exclude_credentials = build_exclude_credentials(user.passkeys.filter(is_active=True))
    options = get_registration_options_for_user(user, exclude_credentials=exclude_credentials)

    request.session['passkey_registration_challenge'] = options['challenge']

    return JsonResponse(options)


@login_required
@require_POST
def finish_passkey_registration_view(request):
    user = request.user
    payload = _json_body(request)

    expected_challenge = request.session.get('passkey_registration_challenge')
    if not expected_challenge:
        return JsonResponse({'ok': False, 'error': 'Registration challenge табылмады.'}, status=400)

    try:
        verification = verify_registration_credential(
            credential=payload,
            expected_challenge=expected_challenge,
        )

        credential_id = payload.get('id')
        transports = payload.get('response', {}).get('transports', [])

        passkey_name = payload.get('device_name') or 'Менің құрылғым'

        PasskeyCredential.objects.create(
            user=user,
            name=passkey_name,
            credential_id=credential_id,
            public_key=bytes_to_base64url(verification.credential_public_key),
            sign_count=verification.sign_count,
            transports=transports,
            aaguid=str(getattr(verification, 'aaguid', '') or ''),
        )

        request.session.pop('passkey_registration_challenge', None)

        log_security_event(
            event_type='passkey_registered',
            request=request,
            user=user,
            description='Қолданушы жаңа passkey тіркеді.',
        )

        return JsonResponse({'ok': True})

    except Exception as exc:
        log_security_event(
            event_type='passkey_auth_failed',
            request=request,
            user=user,
            description=f'Passkey registration сәтсіз: {exc}',
        )
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)


@require_GET
def begin_passkey_authentication_view(request):
    options = get_authentication_options()
    request.session['passkey_auth_challenge'] = options['challenge']
    return JsonResponse(options)


@require_POST
def finish_passkey_authentication_view(request):
    payload = _json_body(request)

    expected_challenge = request.session.get('passkey_auth_challenge')
    credential_id = payload.get('id')

    if not expected_challenge or not credential_id:
        return JsonResponse({'ok': False, 'error': 'Authentication challenge немесе credential_id жоқ.'}, status=400)

    passkey = PasskeyCredential.objects.filter(
        credential_id=credential_id,
        is_active=True,
    ).select_related('user').first()

    if not passkey:
        return JsonResponse({'ok': False, 'error': 'Passkey табылмады.'}, status=404)

    try:
        verification = verify_authentication_credential(
            credential=payload,
            expected_challenge=expected_challenge,
            credential_public_key=passkey.public_key,
            credential_current_sign_count=passkey.sign_count,
        )

        passkey.sign_count = verification.new_sign_count
        passkey.last_used_at = timezone.now()
        passkey.save(update_fields=['sign_count', 'last_used_at', 'updated_at'])

        user = passkey.user

        log_security_event(
            event_type='passkey_auth_passed',
            request=request,
            user=user,
            description='Passkey тексеруі сәтті өтті.',
        )

        request.session.pop('passkey_auth_challenge', None)

        if getattr(user, 'is_2fa_enabled', False):
            request.session['pre_2fa_user_id'] = user.id
            request.session['pre_2fa_username'] = user.username
            request.session['pre_2fa_via_passkey'] = True

            return JsonResponse({
                'ok': True,
                'requires_2fa': True,
                'redirect_url': reverse('verify_2fa'),
            })

        login(request, user, backend='core.utils.backends.EmailOrUsernameModelBackend')

        log_security_event(
            event_type='login_success',
            request=request,
            user=user,
            description='Қолданушы passkey арқылы жүйеге сәтті кірді.',
        )

        return JsonResponse({
            'ok': True,
            'requires_2fa': False,
            'redirect_url': reverse('student'),
        })

    except Exception as exc:
        log_security_event(
            event_type='passkey_auth_failed',
            request=request,
            user=passkey.user,
            description=f'Passkey authentication сәтсіз: {exc}',
        )
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)


@login_required
@require_POST
def remove_passkey_view(request, pk):
    passkey = request.user.passkeys.filter(pk=pk, is_active=True).first()
    if not passkey:
        messages.error(request, 'Passkey табылмады.')
        return redirect('settings')

    passkey.is_active = False
    passkey.save(update_fields=['is_active', 'updated_at'])

    log_security_event(
        event_type='passkey_removed',
        request=request,
        user=request.user,
        description='Қолданушы passkey-ді өшірді.',
    )

    messages.success(request, 'Passkey өшірілді.')
    return redirect('settings')
