from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from core.forms.subjects import SubjectAdminForm, LessonAdminForm
from core.models import Subject, Chapter, Lesson, LessonDocs
from django_summernote.admin import SummernoteModelAdmin, SummernoteModelAdminMixin
from core.models.tasks import Task


# Subject admin
# ----------------------------------------------------------------------------------------------------------------------
# Chapter Tab
class ChapterTab(admin.TabularInline):
    model = Chapter
    fields = ('order', 'name', )
    extra = 0


# Lesson Tab
class LessonTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = Lesson
    fields = ('order', 'title', 'chapter', 'view_link', )
    extra = 0
    readonly_fields = ('view_link', )

    def view_link(self, obj):
        if obj.pk:
            url = reverse('admin:core_lesson_change', args=[obj.pk])
            return format_html('<a href="{}" class="view-link">Толығырақ</a>', url)
        return '-'

    view_link.short_description = _('Сабақ сілтемесі')

    # Chapter choice
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'chapter':
            subject_id = request.resolver_match.kwargs.get('object_id')
            if subject_id:
                kwargs['queryset'] = Chapter.objects.filter(subject_id=subject_id)
            else:
                kwargs['queryset'] = Chapter.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Subject admin
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'last_update')
    search_fields = ('name', 'description', )
    inlines = (ChapterTab, LessonTab, )
    form = SubjectAdminForm


# Chapter admin
# ----------------------------------------------------------------------------------------------------------------------
@admin.register(Chapter)
class ChapterAdmin(SummernoteModelAdmin):
    list_display = ('name', 'subject', 'order', )
    search_fields = ('name', 'subject', )
    list_filter = ('subject', )
    ordering = ('order', )
    inlines = (LessonTab, )


# Lesson admin
# ----------------------------------------------------------------------------------------------------------------------
# LessonDocs Tab
class LessonDocsTab(admin.TabularInline):
    model = LessonDocs
    extra = 0


# Task Tab
class TaskTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = Task
    fields = ('order', 'task_type', 'rating', 'duration', 'view_link', )
    extra = 0
    readonly_fields = ('view_link',)

    def view_link(self, obj):
        if obj.pk:
            url = reverse('admin:core_task_change', args=[obj.pk])
            return format_html('<a href="{}" class="view-link">Толығырақ</a>', url)
        return '-'

    view_link.short_description = _('Тапсырма сілтемесі')


# Lesson admin
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'chapter', 'order', )
    search_fields = ('title', 'subject', 'chapter', 'description', )
    list_filter = ('subject', 'chapter', )
    ordering = ('order', )
    inlines = (LessonDocsTab, TaskTab, )
    readonly_fields = ('subject_link', )
    form = LessonAdminForm


    def subject_link(self, obj):
        if obj.subject:
            url = reverse('admin:core_subject_change', args=[obj.subject.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.subject.name)
        return '-'

    subject_link.short_description = 'Пәнге сілтеме'
