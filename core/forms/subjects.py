from ckeditor.widgets import CKEditorWidget
from django import forms
from core.models import Subject, Lesson, Task, Theory, Question, Option


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