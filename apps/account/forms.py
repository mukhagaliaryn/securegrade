from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core.models import User


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_('Бұл email бойынша аккаунт бұрыннан тіркелген.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.user_type = 'student'
        user.email_verified = False
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'avatar', )


class DeleteAccountForm(forms.Form):
    password = forms.CharField(
        label=_('Қазіргі пароль'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
    confirm = forms.BooleanField(
        label=_('Аккаунтты жоюды растаймын'),
        required=True,
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.user or not self.user.check_password(password):
            raise ValidationError(_('Қазіргі пароль қате енгізілді.'))
        return password


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label=_('Электронды пошта'),
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'example@example.com',
        }),
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_('Жаңа пароль'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_('Жаңа парольді қайталау'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )


class ResendVerificationEmailForm(forms.Form):
    email = forms.EmailField(
        label='Электронды пошта',
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'example@example.com',
        })
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()



class TwoFactorVerifyForm(forms.Form):
    code = forms.CharField(
        label='6 таңбалы код немесе backup code',
        max_length=32,
        widget=forms.TextInput(attrs={
            'autocomplete': 'one-time-code',
            'placeholder': '123456 немесе A1B2C3D4'
        })
    )


class TwoFactorDisableForm(forms.Form):
    password = forms.CharField(
        label='Қазіргі пароль',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'})
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.user or not self.user.check_password(password):
            raise ValidationError('Қазіргі пароль қате.')
        return password


class TwoFactorSetupForm(forms.Form):
    code = forms.CharField(
        label='Authenticator код',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'autocomplete': 'one-time-code',
            'placeholder': '123456'
        })
    )