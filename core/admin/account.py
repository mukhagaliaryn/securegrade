from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as UserModelAdmin
from django.contrib.auth.models import Group
from core.models import LoginAttempt, SecurityEvent, User


class SecurityEventInline(admin.TabularInline):
    model = SecurityEvent
    extra = 0


@admin.register(User)
class UserAdmin(UserModelAdmin):
    model = User
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    list_filter = ('user_type', 'email_verified', 'is_2fa_enabled', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name',)
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('avatar', 'username', 'email', 'first_name', 'last_name', 'user_type', 'password')}),
        (_('Рұқсаттама деректері'), {'fields': ('is_staff', 'is_active', 'is_superuser', 'user_permissions')}),
        (_('Қауіпсіздік деректері'), {'fields': (
            'last_login',
            'email_verified',
            'email_verification_sent_at',
            'is_2fa_enabled',
            'otp_secret',
            'backup_codes',
        )}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2',)}
        ),
    )

    inlines = (SecurityEventInline, )


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'is_successful', 'created_at')
    list_filter = ('is_successful', 'created_at')
    search_fields = ('username', 'ip_address', 'user_agent')
    readonly_fields = ('username', 'ip_address', 'user_agent', 'is_successful', 'created_at')


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'ip_address', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'ip_address', 'description')
    readonly_fields = ('user', 'event_type', 'ip_address', 'user_agent', 'description', 'created_at')



admin.site.unregister(Group)
