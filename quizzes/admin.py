from django.contrib import admin

# Register your models here.
from .models import Quiz,Question,QuizAnswer,QuizResult,Choice

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(QuizResult)
admin.site.register(QuizAnswer)
admin.site.register(Choice)