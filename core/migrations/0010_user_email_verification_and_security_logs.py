from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_remove_task_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False, verbose_name='Email расталды'),
        ),
        migrations.AddField(
            model_name='user',
            name='email_verification_sent_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Email растау хаты жіберілген уақыт'),
        ),
        migrations.CreateModel(
            name='LoginAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, max_length=150, verbose_name='Пайдаланушы аты немесе email')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP мекенжайы')),
                ('user_agent', models.TextField(blank=True, verbose_name='User-Agent')),
                ('is_successful', models.BooleanField(default=False, verbose_name='Сәтті ме')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Жасалған уақыты')),
            ],
            options={
                'verbose_name': 'Кіру әрекеті',
                'verbose_name_plural': 'Кіру әрекеттері',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='SecurityEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('login_success', 'Сәтті кіру'), ('login_failed', 'Сәтсіз кіру'), ('logout', 'Шығу'), ('register', 'Тіркелу'), ('password_changed', 'Құпиясөз өзгертілді'), ('account_deleted', 'Аккаунт жойылды'), ('profile_updated', 'Профиль жаңартылды')], max_length=64, verbose_name='Оқиға түрі')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP мекенжайы')),
                ('user_agent', models.TextField(blank=True, verbose_name='User-Agent')),
                ('description', models.TextField(blank=True, verbose_name='Сипаттама')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Жасалған уақыты')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='security_events', to=settings.AUTH_USER_MODEL, verbose_name='Қолданушы')),
            ],
            options={
                'verbose_name': 'Қауіпсіздік оқиғасы',
                'verbose_name_plural': 'Қауіпсіздік оқиғалары',
                'ordering': ('-created_at',),
            },
        ),
    ]
