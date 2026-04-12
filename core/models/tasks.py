from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Lesson


# Task model
# ----------------------------------------------------------------------------------------------------------------------
class Task(models.Model):
    TASK_TYPE = (
        ('theory', _('Теория')),
        ('video', _('Видеосабақ')),
        ('test', _('Тестілеу')),
        ('simulator', _('Симулятор'))
    )

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE,
        related_name='tasks', verbose_name=_('Сабақ')
    )
    task_type = models.CharField(_('Тапсырма түрі'), choices=TASK_TYPE, default='theory', max_length=32)
    rating = models.PositiveIntegerField(_('Жалпы бағасы'), default=0)
    duration = models.PositiveSmallIntegerField(_('Тапсырма уақыты (мин)'), default=0)
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return self.get_task_type_display()

    class Meta:
        verbose_name = _('Тапсырма')
        verbose_name_plural = _('Тапсырмалар')
        ordering = ('order', )



# Task type: Theory model
# ----------------------------------------------------------------------------------------------------------------------
class Theory(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, null=True,
        verbose_name=_('Тапсырма'), related_name='theories'
    )
    content = models.TextField(_('Теория мәтіні'), blank=True, null=True)
    file = models.FileField(_('Файл'), upload_to='theory/', blank=True, null=True)
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return f'{self.pk} - теория'

    class Meta:
        verbose_name = _('Теория')
        verbose_name_plural = _('Теориялар')
        ordering = ('order', )


# Task type: Video model
# ----------------------------------------------------------------------------------------------------------------------
class Video(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, null=True,
        verbose_name=_('Контент'), related_name='videos'
    )
    url = models.TextField(_('URL сілтеме'))
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return f'{self.pk} - видеосабақ'

    class Meta:
        verbose_name = _('Видеосабақ')
        verbose_name_plural = _('Видеосабақтар')
        ordering = ('order', )


# Task type: Test model
# ----------------------------------------------------------------------------------------------------------------------
# Question model
class Question(models.Model):
    QUESTION_TYPE = (
        ('simple', _('Бір жауапты')),
        ('multiple', _('Көп жауапты')),
    )
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, null=True,
        related_name='questions', verbose_name=_('Тапсырма')
    )
    text = models.TextField(_('Сұрақ'))
    question_type = models.CharField(_('Сұрақтың түрі'), choices=QUESTION_TYPE, default='simple', max_length=32)
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return f'Тест: {self.pk} - сұрақ'

    class Meta:
        verbose_name = _('Тест сұрағы')
        verbose_name_plural = _('Тест сұрақтары')
        ordering = ('order', )


# Option model
class Option(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE,
        related_name='options', verbose_name=_('Сұрақ')
    )
    text = models.TextField(_('Жауап'), blank=True, null=True)
    is_correct = models.BooleanField(_('Дұрыс жауап'), default=False)
    score = models.PositiveIntegerField(_('Балл'), default=0)

    def __str__(self):
        return f'Тест: {self.pk} - жауап'

    class Meta:
        verbose_name = _('Жауап')
        verbose_name_plural = _('Жауаптар')


# Task type: Simulator model
# ----------------------------------------------------------------------------------------------------------------------
class Simulator(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, null=True,
        verbose_name=_('Тапсырма'), related_name='simulators'
    )
    url = models.CharField(_('URL сілтеме'), max_length=300)
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return f'{self.pk} - симулятор'

    class Meta:
        verbose_name = _('Симулятор')
        verbose_name_plural = _('Симуляторлар')
        ordering = ('order', )