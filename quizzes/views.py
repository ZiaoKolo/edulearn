from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from django.forms import formset_factory, modelformset_factory
from datetime import timedelta

from .models import Quiz, Question, Choice, QuizResult, QuizAnswer
from courses.models import Course, Chapter
from .forms import QuizForm, QuestionForm, ChoiceFormSet, TextAnswerForm
from users.models import User

import time

@login_required
def quiz_list(request, course_id):
    """View all quizzes for a specific course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled or is the teacher
    if request.user != course.teacher and request.user not in course.students.all():
        messages.error(request, "Vous devez être inscrit à ce cours pour voir les quiz.")
        return redirect('courses:course_detail', course_id=course_id)
    
    quizzes = Quiz.objects.filter(course=course)
    
    # For students, get their results
    if request.user.is_student():
        results = QuizResult.objects.filter(
            quiz__in=quizzes,
            student=request.user
        ).select_related('quiz')
        results_dict = {result.quiz.id: result for result in results}
    else:
        results_dict = {}
    
    context = {
        'quizzes': quizzes,
        'course': course,
        'results_dict': results_dict,
    }
    
    return render(request, 'quizzes/quiz_list.html', context)

@login_required
def quiz_detail(request, quiz_id):
    """View quiz details"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if user is enrolled or is the teacher
    if request.user != quiz.course.teacher and request.user not in quiz.course.students.all():
        messages.error(request, "Vous devez être inscrit à ce cours pour voir ce quiz.")
        return redirect('courses:course_detail', course_id=quiz.course.id)
    
    # For students, check if they've already completed the quiz
    if request.user.is_student():
        user_results = QuizResult.objects.filter(quiz=quiz, student=request.user).order_by('-completed_at').first()
    else:
        user_results = None
    
    questions = Question.objects.filter(quiz=quiz).prefetch_related('choices')
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'user_results': user_results,
        'course': quiz.course,
    }
    
    return render(request, 'quizzes/quiz_detail.html', context)
@login_required
def take_quiz(request, quiz_id):
    """Start taking a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Verify that the user is enrolled in the course
    if request.user not in quiz.course.students.all():
        messages.error(request, "Vous devez être inscrit à ce cours pour faire ce quiz.")
        return redirect('courses:course_detail', course_id=quiz.course.id)
    
    # Check if user has already completed the quiz
    if QuizResult.objects.filter(quiz=quiz, student=request.user).exists():
        messages.info(request, "Vous avez déjà complété ce quiz. Voici vos résultats.")
        return redirect('quizzes:quiz_result', quiz_id=quiz_id)
    
    questions = Question.objects.filter(quiz=quiz).prefetch_related('choices')
    
    # Store quiz start time in session and calculate end time
    start_time = timezone.now()
    request.session['quiz_start_time'] = start_time.timestamp()
    
    # Calculate end time if there's a time limit
    end_time = None
    if quiz.time_limit:
        end_time = start_time + timedelta(minutes=quiz.time_limit)
        
    context = {
        'quiz': quiz,
        'questions': questions,
        'start_time': start_time,
        'end_time': end_time,
    }
    
    return render(request, 'quizzes/take_quiz.html', context)

@login_required
def submit_quiz(request, quiz_id):
    """Process quiz submission"""
    if request.method != 'POST':
        return redirect('quizzes:quiz_list', course_id=quiz_id)
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz).prefetch_related('choices')
    
    # Calculate time taken
    start_time = request.session.get('quiz_start_time')
    if start_time:
        time_taken = int(timezone.now().timestamp() - float(start_time))
        # Clear from the session
        del request.session['quiz_start_time']
    else:
        time_taken = None
    
    # Check if time limit exceeded (if there is a time limit)
    if quiz.time_limit and time_taken > quiz.time_limit * 60:
        messages.warning(request, f"Attention: Vous avez dépassé le temps limite de {quiz.time_limit} minutes pour ce quiz.")
    
    # Create quiz result
    total_points = questions.aggregate(Sum('points'))['points__sum'] or 0
    quiz_result = QuizResult.objects.create(
        quiz=quiz,
        student=request.user,
        score=0,  # Will be updated as we process answers
        max_score=total_points,
        time_taken=time_taken
    )
    
    score = 0
    
    # Process each question
    for question in questions:
        is_correct = False
        
        if question.question_type == Question.TEXT_ANSWER:
            # Process text answer
            text_answer = request.POST.get(f'question_{question.id}', '').strip()
            
            # Create answer record
            answer = QuizAnswer.objects.create(
                quiz_result=quiz_result,
                question=question,
                text_answer=text_answer,
                is_correct=False  # Will be manually graded later
            )
            
        else:  # Multiple or single choice
            selected_choices_ids = request.POST.getlist(f'question_{question.id}', [])
            selected_choices = Choice.objects.filter(id__in=selected_choices_ids, question=question)
            
            # Create answer record
            answer = QuizAnswer.objects.create(
                quiz_result=quiz_result,
                question=question,
                is_correct=False  # Default, will update below
            )
            answer.selected_choices.set(selected_choices)
            
            # Check if correct for auto-grading
            if question.question_type == Question.MULTIPLE_CHOICE:
                # All correct options must be selected, and no incorrect ones
                correct_choices = Choice.objects.filter(question=question, is_correct=True)
                incorrect_selected = selected_choices.filter(is_correct=False).exists()
                all_correct_selected = set(selected_choices.filter(is_correct=True)) == set(correct_choices)
                
                is_correct = all_correct_selected and not incorrect_selected
                
            else:  # SINGLE_CHOICE
                is_correct = selected_choices.filter(is_correct=True).exists() if selected_choices else False
            
            if is_correct:
                score += question.points
                answer.is_correct = True
                answer.save()
    
    # Update the final score
    quiz_result.score = score
    quiz_result.save()
    
    return redirect('quizzes:quiz_result', quiz_id=quiz.id)

@login_required
def quiz_result(request, quiz_id):
    """View quiz results for a student"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Verify that the user is either the course teacher or the student who took the quiz
    if request.user != quiz.course.teacher and request.user not in quiz.course.students.all():
        messages.error(request, "Vous n'avez pas accès à ces résultats.")
        return redirect('courses:course_detail', course_id=quiz.course.id)
    
    # Get the latest result if user is a student
    if request.user.is_student():
        quiz_result = get_object_or_404(QuizResult, quiz=quiz, student=request.user)
        quiz_answers = QuizAnswer.objects.filter(quiz_result=quiz_result).select_related('question')
    else:
        # If teacher, show all results
        student_id = request.GET.get('student_id')
        if student_id:
            student = get_object_or_404(User, id=student_id)
            quiz_result = get_object_or_404(QuizResult, quiz=quiz, student=student)
            quiz_answers = QuizAnswer.objects.filter(quiz_result=quiz_result).select_related('question')
        else:
            quiz_result = None
            quiz_answers = None
            student_results = QuizResult.objects.filter(quiz=quiz).select_related('student')
            context = {
                'quiz': quiz,
                'student_results': student_results,
                'course': quiz.course,
            }
            return render(request, 'quizzes/teacher_quiz_results.html', context)
    
    context = {
        'quiz': quiz,
        'quiz_result': quiz_result,
        'quiz_answers': quiz_answers,
        'course': quiz.course,
    }
    
    return render(request, 'quizzes/quiz_result.html', context)

@login_required
def create_quiz(request, course_id):
    """Create a new quiz for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Only the teacher of the course can create quizzes
    if request.user != course.teacher:
        messages.error(request, "Seul l'enseignant du cours peut créer des quiz.")
        return redirect('courses:course_detail', course_id=course.id)
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course
            quiz.save()
            
            messages.success(request, "Quiz créé avec succès. Ajoutez maintenant des questions.")
            return redirect('quizzes:add_question', quiz_id=quiz.id)
    else:
        form = QuizForm()
        form.fields['chapter'].queryset = Chapter.objects.filter(course=course)
    
    context = {
        'form': form,
        'course': course,
    }
    
    return render(request, 'quizzes/create_quiz.html', context)

@login_required
def add_question(request, quiz_id):
    """Add a question to a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Only the teacher of the course can add questions
    if request.user != quiz.course.teacher:
        messages.error(request, "Seul l'enseignant du cours peut ajouter des questions.")
        return redirect('courses:course_detail', course_id=quiz.course.id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question_type = form.cleaned_data['question_type']
            question.question_type = question_type
            
            # Set question order
            order = Question.objects.filter(quiz=quiz).count() + 1
            question.order = order
            
            question.save()
            
            # For text answer questions, no choices needed
            if question_type != Question.TEXT_ANSWER:
                return redirect('quizzes:add_choices', question_id=question.id)
            else:
                messages.success(request, "Question à réponse libre ajoutée avec succès.")
                return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuestionForm()
    
    context = {
        'form': form,
        'quiz': quiz,
    }
    
    return render(request, 'quizzes/add_question.html', context)

@login_required
def add_choices(request, question_id):
    """Add choices to a question"""
    question = get_object_or_404(Question, id=question_id)
    
    # Only the teacher of the course can add choices
    if request.user != question.quiz.course.teacher:
        messages.error(request, "Seul l'enseignant du cours peut ajouter des choix.")
        return redirect('courses:course_detail', course_id=question.quiz.course.id)
    
    # Redirect if question type is TEXT_ANSWER
    if question.question_type == Question.TEXT_ANSWER:
        return redirect('quizzes:quiz_detail', quiz_id=question.quiz.id)
    
    if request.method == 'POST':
        formset = ChoiceFormSet(request.POST, prefix='choices')
        
        if formset.is_valid():
            # Save each choice
            for form in formset:
                if form is not None and form.cleaned_data and form.cleaned_data.get('text'):
                    choice = form.save(commit=False)
                    choice.question = question
                    choice.save()
            
            messages.success(request, "Choix ajoutés avec succès.")
            
            # Check if we need to add more questions
            add_more = request.POST.get('add_more')
            if add_more == 'yes':
                return redirect('quizzes:add_question', quiz_id=question.quiz.id)
            else:
                return redirect('quizzes:quiz_detail', quiz_id=question.quiz.id)
    else:
        # Create empty choice forms
        num_forms = 4  # Default number of choice options
        formset = ChoiceFormSet(prefix='choices', queryset=Choice.objects.none())
    
    context = {
        'formset': formset,
        'question': question,
        'quiz': question.quiz,
    }
    
    return render(request, 'quizzes/add_choices.html', context)

@login_required
def edit_quiz(request, quiz_id):
    """Edit quiz details"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Only the teacher of the course can edit the quiz
    if request.user != quiz.course.teacher:
        messages.error(request, "Seul l'enseignant du cours peut modifier ce quiz.")
        return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Quiz modifié avec succès.")
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm(instance=quiz)
        form.fields['chapter'].queryset = Chapter.objects.filter(course=quiz.course)
    
    context = {
        'form': form,
        'quiz': quiz,
    }
    
    return render(request, 'quizzes/edit_quiz.html', context)

@login_required
def delete_quiz(request, quiz_id):
    """Delete a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course_id = quiz.course.id
    
    # Only the teacher of the course can delete the quiz
    if request.user != quiz.course.teacher:
        messages.error(request, "Seul l'enseignant du cours peut supprimer ce quiz.")
        return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, "Quiz supprimé avec succès.")
        return redirect('quizzes:quiz_list', course_id=course_id)
    
    context = {
        'quiz': quiz,
    }
    
    return render(request, 'quizzes/delete_quiz.html', context)

@login_required
def edit_question(request, question_id):
    """Edit a question"""
    question = get_object_or_404(Question, id=question_id)
    
    # Only the teacher of the course can edit questions
    if request.user != question.quiz.course.teacher:
        messages.error(request, "Seul l'enseignant du cours peut modifier cette question.")
        return redirect('quizzes:quiz_detail', quiz_id=question.quiz.id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        
        if form.is_valid():
            question = form.save()
            messages.success(request, "Question modifiée avec succès.")
            
            # If question type changed to TEXT_ANSWER, remove all choices
            if question.question_type == Question.TEXT_ANSWER:
                Choice.objects.filter(question=question).delete()
                return redirect('quizzes:quiz_detail', quiz_id=question.quiz.id)
            else:
                return redirect('quizzes:edit_choices', question_id=question.id)
    else:
        form = QuestionForm(instance=question)
    
    context = {
        'form': form,
        'question': question,
        'quiz': question.quiz,
    }
    
    return render(request, 'quizzes/edit_question.html', context)

@login_required
def edit_choices(request, question_id):
    """Edit choices for a question"""
    question = get_object_or_404(Question, id=question_id)
    
    # Only the teacher of the course can edit choices
    if request.user != question.quiz.course.teacher:
        messages.error(request, "Seul l'enseignant du cours peut modifier ces choix.")
        return redirect('quizzes:quiz_detail', quiz_id=question.quiz.id)
    
    # Redirect if question type is TEXT_ANSWER
    if question.question_type == Question.TEXT_ANSWER:
        return redirect('quizzes:quiz_detail', quiz_id=question.quiz.id)
    
    ChoiceModelFormSet = modelformset_factory(Choice, fields=('text', 'is_correct'), extra=1)
    
    if request.method == 'POST':
        formset = ChoiceModelFormSet(request.POST, queryset=Choice.objects.filter(question=question))
        
        if formset.is_valid():
            formset.save()
            messages.success(request, "Choix modifiés avec succès.")
            return redirect('quizzes:quiz_detail', quiz_id=question.quiz.id)
    else:
        formset = ChoiceModelFormSet(queryset=Choice.objects.filter(question=question))
    
    context = {
        'formset': formset,
        'question': question,
        'quiz': question.quiz,
    }
    
    return render(request, 'quizzes/edit_choices.html', context)

@login_required
def delete_question(request, question_id):
    """Delete a question"""
    question = get_object_or_404(Question, id=question_id)
    quiz_id = question.quiz.id
    
    # Only the teacher of the course can delete questions
    if request.user != question.quiz.course.teacher:
        messages.error(request, "Seul l'enseignant du cours peut supprimer cette question.")
        return redirect('quizzes:quiz_detail', quiz_id=quiz_id)
    
    if request.method == 'POST':
        question.delete()
        # Reorder remaining questions
        questions = Question.objects.filter(quiz_id=quiz_id).order_by('order')
        for i, q in enumerate(questions, 1):
            q.order = i
            q.save()
            
        messages.success(request, "Question supprimée avec succès.")
        return redirect('quizzes:quiz_detail', quiz_id=quiz_id)
    
    context = {
        'question': question,
        'quiz': question.quiz,
    }
    
    return render(request, 'quizzes/delete_question.html', context)

@login_required
def grade_text_answer(request, answer_id):
    """Grade a text answer (for teacher)"""
    answer = get_object_or_404(QuizAnswer, id=answer_id)
    
    # Only the teacher of the course can grade answers
    if request.user != answer.quiz_result.quiz.course.teacher:
        messages.error(request, "Seul l'enseignant du cours peut noter les réponses.")
        return redirect('courses:course_detail', course_id=answer.quiz_result.quiz.course.id)
    
    if request.method == 'POST':
        is_correct = request.POST.get('is_correct') == 'true'
        answer.is_correct = is_correct
        answer.save()
        
        # Update the quiz result score
        quiz_result = answer.quiz_result
        total_correct_points = QuizAnswer.objects.filter(
            quiz_result=quiz_result,
            is_correct=True
        ).aggregate(Sum('question__points'))['question__points__sum'] or 0
        
        quiz_result.score = total_correct_points
        quiz_result.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)

@login_required
def analytics_quiz(request, quiz_id):
    """View analytics for a quiz (for teacher)"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Only the teacher of the course can view analytics
    if request.user != quiz.course.teacher:
        messages.error(request, "Seul l'enseignant du cours peut voir les analyses.")
        return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    
    # Get all results for this quiz
    results = QuizResult.objects.filter(quiz=quiz).select_related('student')
    
    # Calculate average score
    avg_score = results.aggregate(avg_score=Sum('score') / Count('id'))['avg_score'] or 0
    
    # Calculate completion rate
    total_students = quiz.course.students.count()
    completed_students = results.count()
    completion_rate = (completed_students / total_students * 100) if total_students > 0 else 0
    
    # Get performance by question
    questions = Question.objects.filter(quiz=quiz)
    question_stats = []
    
    for question in questions:
        correct_count = QuizAnswer.objects.filter(
            question=question,
            is_correct=True
        ).count()
        
        total_attempts = QuizAnswer.objects.filter(question=question).count()
        success_rate = (correct_count / total_attempts * 100) if total_attempts > 0 else 0
        
        question_stats.append({
            'question': question,
            'success_rate': success_rate,
            'correct_count': correct_count,
            'total_attempts': total_attempts,
        })
    
    context = {
        'quiz': quiz,
        'results': results,
        'avg_score': avg_score,
        'completion_rate': completion_rate,
        'question_stats': question_stats,
        'total_students': total_students,
        'completed_students': completed_students,
    }
    
    return render(request, 'quizzes/analytics_quiz.html', context)
@login_required
def teacher_quizzes(request):
    """View all quizzes created by the teacher"""
    # Check if user is a teacher
    if not request.user.is_teacher():
        messages.error(request, "Seuls les enseignants peuvent accéder à cette page.")
        return redirect('dashboard:student_dashboard')
    
    # Get all courses taught by this teacher
    teaching_courses = Course.objects.filter(teacher=request.user)
    
    # Get all quizzes for these courses
    quizzes = Quiz.objects.filter(course__in=teaching_courses).select_related('course')
    
    context = {
        'quizzes': quizzes,
        'teaching_courses': teaching_courses,
    }
    
    return render(request, 'quizzes/teacher_quizzes.html', context)