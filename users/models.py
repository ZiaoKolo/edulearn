# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (STUDENT, 'Élève'),
        (TEACHER, 'Enseignant'),
        (ADMIN, 'Administrateur'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    def is_student(self):
        return self.role == self.STUDENT
        
    def is_teacher(self):
        return self.role == self.TEACHER
    
    def is_admin_user(self):
        return self.role == self.ADMIN and self.is_active
    
    def save(self, *args, **kwargs):
        # Pour les nouveaux utilisateurs (sans ID), bloquer la création d'administrateurs
        if not self.id and self.role == self.ADMIN:
            # Changer le rôle par défaut à enseignant pour plus de privilèges
            self.role = self.TEACHER
        super().save(*args, **kwargs)