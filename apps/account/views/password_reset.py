from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from apps.account.forms import CustomPasswordResetForm, CustomSetPasswordForm
from apps.account.security import log_security_event

User = get_user_model()


class SecurePasswordResetView(PasswordResetView):
    template_name = 'app/account/password_reset/page.html'
    email_template_name = 'app/account/emails/password_reset_email.txt'
    html_email_template_name = 'app/account/emails/password_reset_email.html'
    subject_template_name = 'app/account/emails/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        email = form.cleaned_data.get('email', '').strip().lower()

        user = User.objects.filter(email__iexact=email).first()
        if user:
            log_security_event(
                event_type='password_reset_requested',
                request=self.request,
                user=user,
                description=_('Құпиясөзді қалпына келтіру сілтемесі сұралды.'),
            )
        else:
            log_security_event(
                event_type='password_reset_requested',
                request=self.request,
                description=_('Тіркелмеген email үшін құпиясөзді қалпына келтіру әрекеті жасалды.'),
            )

        messages.success(
            self.request,
            _('Егер бұл email жүйеде тіркелген болса, құпиясөзді қалпына келтіру сілтемесі жіберілді.'),
        )
        return super().form_valid(form)


class SecurePasswordResetDoneView(PasswordResetDoneView):
    template_name = 'app/account/password_reset/done.html'


class SecurePasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'app/account/password_reset/confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.user
        log_security_event(
            event_type='password_reset_completed',
            request=self.request,
            user=user,
            description=_('Қолданушы құпиясөзін reset flow арқылы жаңартты.'),
        )
        messages.success(
            self.request,
            _('Құпиясөз сәтті жаңартылды. Енді жаңа парольмен жүйеге кіре аласыз.'),
        )
        return response


class SecurePasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'app/account/password_reset/complete.html'
