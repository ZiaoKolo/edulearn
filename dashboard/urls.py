from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('progress/', views.student_progress, name='student_progress'),
    path('progress/<int:course_id>/', views.student_progress, name='course_progress'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('update-progress/<int:content_id>/', views.update_progress, name='update_progress'),
    path('analytics/course/<int:course_id>/', views.teacher_course_analytics, name='teacher_course_analytics'),
    path('contact-student/<int:student_id>/', views.contact_student, name='contact_student'),
    path('contact-teacher/<int:teacher_id>/', views.contact_teacher, name='contact_teacher'),
    path('assign-quiz/<int:quiz_id>/', views.assign_quiz, name='assign_quiz'),
    path('assigned-quizzes/', views.assigned_quizzes, name='assigned_quizzes'),
]