from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    # Quiz listing and details
    path('course/<int:course_id>/quizzes/', views.quiz_list, name='quiz_list'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    
    # Taking quizzes
    path('quiz/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('quiz/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz/<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),
    
    # Creating and managing quizzes (teacher)
    path('course/<int:course_id>/create-quiz/', views.create_quiz, name='create_quiz'),
    path('quiz/<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('quiz/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    
    # Managing questions
    path('quiz/<int:quiz_id>/add-question/', views.add_question, name='add_question'),
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    
    # Managing choices
    path('question/<int:question_id>/add-choices/', views.add_choices, name='add_choices'),
    path('question/<int:question_id>/edit-choices/', views.edit_choices, name='edit_choices'),
    
    # Grading and analytics
    path('answer/<int:answer_id>/grade/', views.grade_text_answer, name='grade_text_answer'),
    path('quiz/<int:quiz_id>/analytics/', views.analytics_quiz, name='analytics_quiz'),
    # Add this to urlpatterns in urls.py
    path('teacher/quizzes/', views.teacher_quizzes, name='teacher_quizzes'),
]