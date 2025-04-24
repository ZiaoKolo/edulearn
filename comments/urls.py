from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    # Add comment to course or content
    path('add/<str:content_type>/<int:object_id>/', views.add_comment, name='add_comment'),
    
    # List comments for course or content
    path('list/<str:content_type>/<int:object_id>/', views.list_comments, name='list_comments'),
    
    # Edit comment
    path('edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    
    # Delete comment
    path('delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    
    # Vote on comment
    path('vote/<int:comment_id>/', views.vote_comment, name='vote_comment'),
]