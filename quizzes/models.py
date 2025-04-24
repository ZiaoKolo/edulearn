# quizzes/models.py
from django.db import models
from courses.models import Course, Chapter
from users.models import User

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    time_limit = models.PositiveIntegerField(blank=True, null=True, help_text="Temps limite en minutes (optionnel)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Question(models.Model):
    MULTIPLE_CHOICE = 'multiple'
    SINGLE_CHOICE = 'single'
    TEXT_ANSWER = 'text'
    
    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, 'Choix multiple'),
        (SINGLE_CHOICE, 'Choix unique'),
        (TEXT_ANSWER, 'Réponse texte'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=8, choices=QUESTION_TYPES, default=SINGLE_CHOICE)
    order = models.PositiveIntegerField(default=1)
    points = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.text

class QuizResult(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_results')
    score = models.FloatField()
    max_score = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)
    time_taken = models.PositiveIntegerField(help_text="Temps pris en secondes", null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - {self.score}/{self.max_score}"

class QuizAnswer(models.Model):
    quiz_result = models.ForeignKey(QuizResult, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choices = models.ManyToManyField(Choice, blank=True)
    text_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Réponse de {self.quiz_result.student.username} à la question {self.question.order}"
# quizzes/models.py - Ajouter à la fin du fichier

class QuizAssignment(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='assignments')
    students = models.ManyToManyField(User, related_name='assigned_quizzes')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_assignments_given')
    due_date = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quiz.title} - Assigné le {self.assigned_at.strftime('%d/%m/%Y')}"