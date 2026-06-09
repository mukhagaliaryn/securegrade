from ckeditor.widgets import CKEditorWidget
from django import forms
from core.models import Subject, Lesson, Task, Theory, Question, Option, LiveStream


# SubjectAdminForm
# ----------------------------------------------------------------------------------------------------------------------
class SubjectAdminForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = '__all__'
        widgets = {
            'description': CKEditorWidget(config_name='default'),
        }


# LessonAdminForm
# ----------------------------------------------------------------------------------------------------------------------
class LessonAdminForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = '__all__'
        widgets = {
            'description': CKEditorWidget(config_name='default'),
        }


class TheoryAdminForm(forms.ModelForm):
    class Meta:
        model = Theory
        fields = '__all__'
        widgets = {
            'content': CKEditorWidget(config_name='default'),
        }


class QuestionAdminForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'
        widgets = {
            'text': CKEditorWidget(config_name='default'),
        }


class OptionAdminForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = '__all__'
        widgets = {
            'text': CKEditorWidget(config_name='default'),
        }



class LiveStreamForm(forms.ModelForm):
    class Meta:
        model = LiveStream
        fields = [
            'title',
            'description',
            'youtube_url',
            'iframe_code',
            'subject',
            'starts_at',
            'ends_at',
            'is_active',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full rounded-2xl border border-border-200 bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary-500 focus:ring-4 focus:ring-primary-100',
                'placeholder': 'Мысалы: Python кіріспе сабағы',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-2xl border border-border-200 bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary-500 focus:ring-4 focus:ring-primary-100',
                'rows': 4,
                'placeholder': 'Эфир туралы қысқаша ақпарат...',
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': 'w-full rounded-2xl border border-border-200 bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary-500 focus:ring-4 focus:ring-primary-100',
                'placeholder': 'https://www.youtube.com/watch?v=...',
            }),
            'iframe_code': forms.Textarea(attrs={
                'class': 'w-full font-mono rounded-2xl border border-border-200 bg-secondary-50 px-4 py-3 text-xs text-foreground outline-none transition focus:border-primary-500 focus:ring-4 focus:ring-primary-100',
                'rows': 5,
                'placeholder': '<iframe width="100%" height="100%" src="https://www.youtube.com/embed/..." ...></iframe>',
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full rounded-2xl border border-border-200 bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary-500 focus:ring-4 focus:ring-primary-100',
            }),
            'starts_at': forms.DateTimeInput(attrs={
                'class': 'w-full rounded-2xl border border-border-200 bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary-500 focus:ring-4 focus:ring-primary-100',
                'type': 'datetime-local',
            }),
            'ends_at': forms.DateTimeInput(attrs={
                'class': 'w-full rounded-2xl border border-border-200 bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary-500 focus:ring-4 focus:ring-primary-100',
                'type': 'datetime-local',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-border-200 text-primary-600 focus:ring-primary-500',
            }),
        }
