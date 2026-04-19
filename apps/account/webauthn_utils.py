import base64
import json
from typing import Any

from django.conf import settings
from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)


def bytes_to_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('utf-8')


def json_bytes_to_dict(value: Any) -> dict:
    if isinstance(value, str):
        return json.loads(value)
    return json.loads(options_to_json(value))


def get_registration_options_for_user(user, exclude_credentials=None) -> dict:
    exclude_credentials = exclude_credentials or []

    options = generate_registration_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_id=str(user.id).encode('utf-8'),
        user_name=user.username,
        user_display_name=str(user),
        timeout=settings.WEBAUTHN_TIMEOUT,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        supported_pub_key_algs=[
            COSEAlgorithmIdentifier.ECDSA_SHA_256,
            COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
        ],
    )
    return json_bytes_to_dict(options)


def verify_registration_credential(credential: dict, expected_challenge: str):
    verification = verify_registration_response(
        credential=credential,
        expected_challenge=base64url_to_bytes(expected_challenge),
        expected_origin=settings.WEBAUTHN_RP_ORIGIN,
        expected_rp_id=settings.WEBAUTHN_RP_ID,
        require_user_verification=True,
    )
    return verification


def get_authentication_options(allow_credentials=None) -> dict:
    options = generate_authentication_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        timeout=settings.WEBAUTHN_TIMEOUT,
        allow_credentials=allow_credentials or None,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    return json_bytes_to_dict(options)


def verify_authentication_credential(
    credential: dict,
    expected_challenge: str,
    credential_public_key: str,
    credential_current_sign_count: int,
):
    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=base64url_to_bytes(expected_challenge),
        expected_rp_id=settings.WEBAUTHN_RP_ID,
        expected_origin=settings.WEBAUTHN_RP_ORIGIN,
        credential_public_key=base64url_to_bytes(credential_public_key),
        credential_current_sign_count=credential_current_sign_count,
        require_user_verification=True,
    )
    return verification


def build_exclude_credentials(passkeys):
    descriptors = []

    for passkey in passkeys:
        descriptors.append(
            PublicKeyCredentialDescriptor(
                id=base64url_to_bytes(passkey.credential_id),
            )
        )

    return descriptors
