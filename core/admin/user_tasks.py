from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from core.models import UserTask, UserVideo, UserAnswer, UserSimulator, UserTheory


# UserTask admin
# ----------------------------------------------------------------------------------------------------------------------
class UserTheoryTab(admin.TabularInline):
    model = UserTheory
    extra = 0


class UserSimulatorTab(admin.TabularInline):
    model = UserSimulator
    extra = 0


class UserVideoTab(admin.TabularInline):
    model = UserVideo
    extra = 0


class UserAnswerTab(admin.TabularInline):
    model = UserAnswer
    extra = 0


@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('user_lesson', 'task', 'submitted_at', 'rating', 'is_completed', )
    list_filter = ('user_lesson', 'task', 'is_completed', )
    readonly_fields = ('user_lesson_link', )

    def user_lesson_link(self, obj):
        if obj.user_lesson:
            url = reverse('admin:core_userlesson_change', args=[obj.user_lesson.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.user_lesson)
        return '-'

    user_lesson_link.short_description = 'Қолданушының сабағы'

    def get_inline_instances(self, request, obj=None):
        if obj is None or not obj.task:
            return []

        inlines = []

        match obj.task.task_type:
            case 'theory':
                inlines = [UserTheoryTab]
            case 'video':
                inlines = [UserVideoTab]
            case 'test':
                inlines = [UserAnswerTab]
            case 'simulator':
                inlines = [UserSimulatorTab]

        return [inline(self.model, self.admin_site) for inline in inlines]
