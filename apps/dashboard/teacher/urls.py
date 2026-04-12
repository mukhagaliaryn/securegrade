from django.urls import path
from . import views

app_name = 'teacher'

urlpatterns = [
    path('', views.teacher_dashboard_view, name='dashboard'),
    path('user-subject/<int:user_subject_id>/', views.user_subject_detail_view, name='user_subject_detail'),
]