from django.utils.translation import gettext_lazy as _
import re
from urllib.parse import urlparse, parse_qs
from django.conf import settings
from django.db import models
from django.utils import timezone


# Subject model
# ----------------------------------------------------------------------------------------------------------------------
class Subject(models.Model):
    name = models.CharField(_('Атауы'), max_length=255)
    poster = models.ImageField(_('Постер'), blank=True, null=True, upload_to='core/models/subject/posters')
    description = models.TextField(_('Анықтамасы'), blank=True, null=True)
    created_at = models.DateTimeField(_('Уақыты'), auto_now_add=True)
    last_update = models.DateTimeField(_('Соңғы өзгеріс'), auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Пән')
        verbose_name_plural = _('Пәндер')
        ordering = ('created_at', )


# Chapter model
# ----------------------------------------------------------------------------------------------------------------------
class Chapter(models.Model):
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE,
        verbose_name=_('Пән'), related_name='chapters'
    )
    name = models.CharField(_('Атауы'), max_length=255)
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Модуль')
        verbose_name_plural = _('Модульдер')
        ordering = ('order', )


# Lesson model
# ----------------------------------------------------------------------------------------------------------------------
class Lesson(models.Model):
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE,
        verbose_name=_('Пән'), related_name='lessons', null=True, blank=True
    )
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE,
        verbose_name=_('Модуль'), related_name='lessons'
    )
    title = models.CharField(_('Тақырыбы'), max_length=255)
    description = models.TextField(_('Анықтамасы'), blank=True, null=True)
    date_created = models.DateTimeField(_('Жасалған уақыты'), auto_now_add=True)
    last_update = models.DateTimeField(_('Соңғы жаңарту'), auto_now=True)
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return self.title[:64]

    class Meta:
        verbose_name = _('Сабақ')
        verbose_name_plural = _('Сабақтар')
        ordering = ('order', )


# LessonDoc model
# ----------------------------------------------------------------------------------------------------------------------
class LessonDocs(models.Model):
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE,
        verbose_name=_('Сабақ'), related_name='docs'
    )
    title = models.CharField(_('Тақырыбы'), max_length=255)
    file = models.FileField(_('Файл'), upload_to='core/models/lesson/docs/', blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Сабақ құжаты')
        verbose_name_plural = _('Сабақ құжаттары')



# LiveStream
# ----------------------------------------------------------------------------------------------------------------------
class LiveStream(models.Model):
    title = models.CharField('Атауы', max_length=255)
    description = models.TextField('Сипаттама', blank=True)

    youtube_url = models.URLField('YouTube сілтемесі', blank=True)
    iframe_code = models.TextField('YouTube iframe коды')

    subject = models.ForeignKey(
        'core.Subject',
        on_delete=models.CASCADE,
        related_name='live_streams',
        verbose_name='Пән',
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='live_streams',
        verbose_name='Оқытушы',
    )

    starts_at = models.DateTimeField('Басталу уақыты')
    ends_at = models.DateTimeField('Аяқталу уақыты', null=True, blank=True)
    is_active = models.BooleanField('Белсенді', default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['starts_at']
        verbose_name = 'Тікелей эфир'
        verbose_name_plural = 'Тікелей эфирлер'

    def __str__(self):
        return self.title

    @property
    def is_live_now(self):
        now = timezone.now()

        if not self.is_active:
            return False

        if self.ends_at:
            return self.starts_at <= now <= self.ends_at

        return self.starts_at <= now

    @property
    def is_upcoming(self):
        return timezone.now() < self.starts_at

    @property
    def is_finished(self):
        if self.ends_at:
            return timezone.now() > self.ends_at

        return False

