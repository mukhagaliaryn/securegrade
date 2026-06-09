from django.urls import path
from . import views

app_name = 'teacher'

urlpatterns = [
    path('', views.teacher_dashboard_view, name='dashboard'),
    path('user-subject/<int:user_subject_id>/', views.user_subject_detail_view, name='user_subject_detail'),
    path('live-streams/', views.teacher_live_stream_list, name='teacher_live_stream_list'),
    path('live-streams/create/', views.teacher_live_stream_create, name='teacher_live_stream_create'),
    path('live-streams/<int:pk>/', views.teacher_live_stream_detail, name='teacher_live_stream_detail'),
    path('live-streams/<int:pk>/edit/', views.teacher_live_stream_update, name='teacher_live_stream_update'),
    path('live-streams/<int:pk>/delete/', views.teacher_live_stream_delete, name='teacher_live_stream_delete'),
]