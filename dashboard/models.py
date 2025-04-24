# dashboard/models.py
from django.db import models
from users.models import User
from courses.models import Course, Content

class StudentProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='student_progress')
    completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)
    time_spent = models.PositiveIntegerField(default=0, help_text="Temps passé en secondes")
    
    class Meta:
        unique_together = ['student', 'content']
    
    def __str__(self):
        return f"{self.student.username} - {self.content.title}"

class CourseCompletion(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_completions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='completions')
    completion_date = models.DateTimeField(auto_now_add=True)
    certificate_issued = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"

class Notification(models.Model):
    MESSAGE = 'message'
    SYSTEM = 'system'
    ALERT = 'alert'
    
    NOTIFICATION_TYPES = [
        (MESSAGE, 'Message'),
        (SYSTEM, 'System'),
        (ALERT, 'Alert'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default=SYSTEM)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"