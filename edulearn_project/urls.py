from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),  # users.urls should have app_name='users'
    path('dashboard/', include('dashboard.urls')),  # dashboard.urls should have app_name='dashboard'
    path('courses/', include('courses.urls')),  # courses.urls should have app_name='courses'
    path('comments/', include('comments.urls')),  # comments.urls should have app_name='comments'
    path('quizzes/', include('quizzes.urls')),  # quizzes.urls should have app_name='quizzes'
    path('', home_view, name='home'),
]

# Add this if you're using media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)