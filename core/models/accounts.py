from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


# User model
class User(AbstractUser):
    USER_TYPE = (
        ('student', _('Білім алушы')),
        ('teacher', _('Оқытушы')),
        ('admin', _('Администрация')),
    )

    avatar = models.ImageField(_('Сурет'), upload_to='core/account/users/', blank=True, null=True)
    user_type = models.CharField(_('Қолданушы типі'), max_length=32, choices=USER_TYPE, default='student')
    email_verified = models.BooleanField(_('Email расталды'), default=False)
    email_verification_sent_at = models.DateTimeField(
        _('Email растау хаты жіберілген уақыт'), blank=True, null=True
    )

    def __str__(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.username

    class Meta:
        verbose_name = _('Қолданушы')
        verbose_name_plural = _('Қолданушылар')
