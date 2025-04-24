from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course listing and details
    path('', views.course_list, name='course_list'),
    path('subject/<int:subject_id>/', views.course_list_by_subject, name='course_list_by_subject'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    
    # Chapter and content
    path('<int:course_id>/chapters/', views.chapter_list, name='chapter_list'),
    path('chapter/<int:chapter_id>/', views.chapter_detail, name='chapter_detail'),
    path('content/<int:content_id>/', views.content_detail, name='content_detail'),
    
    # Course management (for teachers)
    path('create/', views.course_create, name='create_course'),
    path('<int:course_id>/edit/', views.course_edit, name='edit_course'),
    path('<int:course_id>/delete/', views.course_delete, name='course_delete'),
    
    # Chapter management
    path('<int:course_id>/chapter/create/', views.chapter_create, name='chapter_create'),
    path('chapter/<int:chapter_id>/edit/', views.chapter_edit, name='chapter_edit'),
    path('chapter/<int:chapter_id>/delete/', views.chapter_delete, name='chapter_delete'),
    
    # Content management - Correction ici pour correspondre au template
    path('chapter/<int:chapter_id>/content/create/', views.content_create, name='content_create'),
    path('content/<int:content_id>/edit/', views.content_edit, name='content_edit'),
    path('content/<int:content_id>/delete/', views.content_delete, name='content_delete'),
    
    # Enrollment
    path('<int:course_id>/enroll/', views.course_enroll, name='course_enroll'),
    path('<int:course_id>/unenroll/', views.course_unenroll, name='course_unenroll'),
    
    # Subject management (for admins)
    path('subjects/', views.subject_list, name='subject_list'),
    path('subject/create/', views.subject_create, name='subject_create'),
    path('subject/<int:subject_id>/edit/', views.subject_edit, name='subject_edit'),
    path('subject/<int:subject_id>/delete/', views.subject_delete, name='subject_delete'),
]