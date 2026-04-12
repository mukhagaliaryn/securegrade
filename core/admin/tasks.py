from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django_summernote.admin import SummernoteModelAdmin, SummernoteModelAdminMixin

from core.forms.subjects import TheoryAdminForm, QuestionAdminForm, OptionAdminForm
from core.models import Task, Question, Option, Video, Simulator, Theory


# Task admin
# ----------------------------------------------------------------------------------------------------------------------
class TheoryTab(admin.StackedInline):
    model = Theory
    extra = 0
    form = TheoryAdminForm


class SimulatorTab(admin.TabularInline):
    model = Simulator
    extra = 0


# Video Tab
class VideoTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = Video
    extra = 0


# Question Tab
class QuestionTab(admin.TabularInline):
    model = Question
    fields = ('order', 'text', 'question_type', 'view_link', )
    extra = 0
    readonly_fields = ('view_link', )
    form = QuestionAdminForm

    def view_link(self, obj):
        if obj.pk:
            url = reverse('admin:core_question_change', args=[obj.pk])
            return format_html('<a href="{}" class="view-link">Толығырақ</a>', url)
        return '-'

    view_link.short_description = 'Сұраққа сілтеме'


# ----------------------- Task admin -----------------------
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'rating', 'duration', 'order', )
    readonly_fields = ('lesson_link', )

    def lesson_link(self, obj):
        if obj.lesson:
            url = reverse('admin:core_lesson_change', args=[obj.lesson.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.lesson.title)
        return '-'

    lesson_link.short_description = 'Сабаққа сілтеме'

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []

        inline_instances = []

        if obj.task_type == 'theory':
            inline_instances = [TheoryTab(self.model, self.admin_site)]
        elif obj.task_type == 'video':
            inline_instances = [VideoTab(self.model, self.admin_site)]
        elif obj.task_type == 'test':
            inline_instances = [QuestionTab(self.model, self.admin_site)]
        elif obj.task_type == 'simulator':
            inline_instances = [SimulatorTab(self.model, self.admin_site)]

        return inline_instances


# Task type:Test admin
# ----------------------------------------------------------------------------------------------------------------------
# Option Tab
class OptionTab(admin.TabularInline):
    model = Option
    fields = ('text', 'is_correct', )
    extra = 0
    form = OptionAdminForm


# Question Admin
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    readonly_fields = ('task_link', )
    inlines = (OptionTab, )
    form = QuestionAdminForm

    def task_link(self, obj):
        if obj.task:
            url = reverse('admin:core_task_change', args=[obj.task.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.task)
        return '—'

    task_link.short_description = 'Сұраққа сілтеме'
