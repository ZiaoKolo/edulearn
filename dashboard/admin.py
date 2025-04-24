from django.contrib import admin
from .models import StudentProgress,CourseCompletion,Notification

admin.site.register(StudentProgress)
admin.site.register(CourseCompletion)
admin.site.register(Notification)

# Register your models here.
