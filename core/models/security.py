from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class LoginAttempt(models.Model):
    username = models.CharField(_('Пайдаланушы аты немесе email'), max_length=150, blank=True)
    ip_address = models.GenericIPAddressField(_('IP мекенжайы'), null=True, blank=True)
    user_agent = models.TextField(_('User-Agent'), blank=True)
    is_successful = models.BooleanField(_('Сәтті ме'), default=False)
    created_at = models.DateTimeField(_('Жасалған уақыты'), auto_now_add=True)

    class Meta:
        verbose_name = _('Кіру әрекеті')
        verbose_name_plural = _('Кіру әрекеттері')
        ordering = ('-created_at',)

    def __str__(self):
        status = 'OK' if self.is_successful else 'FAIL'
        return f'{self.username or "unknown"} - {status}'


class SecurityEvent(models.Model):
    EVENT_TYPES = (
        ('login_success', _('Сәтті кіру')),
        ('login_failed', _('Сәтсіз кіру')),
        ('logout', _('Шығу')),
        ('register', _('Тіркелу')),
        ('password_reset_requested', _('Құпия сөзді қалпына келтіру сұралады')),
        ('password_reset_completed', _('Құпия сөзді қалпына келтіру аяқталды')),
        ('password_changed', _('Құпиясөз өзгертілді')),
        ('account_deleted', _('Аккаунт жойылды')),
        ('profile_updated', _('Профиль жаңартылды')),
        ('email_verification_sent', _('Электрондық поштаны тексеру жіберілді')),
        ('email_verified', _('Электрондық пошта расталды')),
        ('2fa_enabled', _('2FA қосулы')),
        ('2fa_disabled', _('2FA өшірулі')),
        ('2fa_challenge_passed', _('2FA процесінен өтті')),
        ('2fa_challenge_failed', _('2FA процесінде қателік кетті')),
        ('2fa_backup_code_used', _('2FA Backup Code Used')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Қолданушы'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_events',
    )
    event_type = models.CharField(_('Оқиға түрі'), max_length=64, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(_('IP мекенжайы'), null=True, blank=True)
    user_agent = models.TextField(_('User-Agent'), blank=True)
    description = models.TextField(_('Сипаттама'), blank=True)
    created_at = models.DateTimeField(_('Жасалған уақыты'), auto_now_add=True)

    class Meta:
        verbose_name = _('Қауіпсіздік оқиғасы')
        verbose_name_plural = _('Қауіпсіздік оқиғалары')
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.get_event_type_display()} - {self.user or "anon"}'


class PasskeyCredential(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='passkeys',
        verbose_name=_('Қолданушы'),
    )
    name = models.CharField(_('Құрылғы атауы'), max_length=255, blank=True)
    credential_id = models.CharField(_('Credential ID'), max_length=512, unique=True)
    public_key = models.TextField(_('Public key'))
    sign_count = models.PositiveBigIntegerField(_('Sign count'), default=0)
    transports = models.JSONField(_('Transports'), default=list, blank=True)
    aaguid = models.CharField(_('AAGUID'), max_length=64, blank=True)
    is_active = models.BooleanField(_('Белсенді'), default=True)
    last_used_at = models.DateTimeField(_('Соңғы қолданылған уақыт'), null=True, blank=True)
    created_at = models.DateTimeField(_('Жасалған уақыт'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Жаңартылған уақыт'), auto_now=True)

    class Meta:
        verbose_name = _('Passkey credential')
        verbose_name_plural = _('Passkey credentials')
        ordering = ('-created_at',)

    def __str__(self):
        return self.name or f'{self.user} - passkey'
