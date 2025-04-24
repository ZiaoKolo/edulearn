# courses/models.py
from django.db import models
from users.models import User

class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_teaching')
    description = models.TextField()
    image = models.ImageField(upload_to='course_images', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    students = models.ManyToManyField(User, related_name='courses_enrolled', blank=True)
    
    def __str__(self):
        return self.title

class Chapter(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Content(models.Model):
    TEXT = 'text'
    VIDEO = 'video'
    PDF = 'pdf'
    IMAGE = 'image'
    
    CONTENT_TYPES = [
        (TEXT, 'Texte'),
        (VIDEO, 'Vidéo'),
        (PDF, 'PDF'),
        (IMAGE, 'Image'),
    ]
    
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=5, choices=CONTENT_TYPES)
    text_content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='course_files', blank=True, null=True)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title
