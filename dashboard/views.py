# dashboard/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F
from .models import StudentProgress, CourseCompletion, Notification
from courses.models import Course, Content, Chapter
from users.models import User
from quizzes.models import Quiz, QuizResult, Question ,QuizAssignment # Importation des modèles de quiz
from datetime import datetime, timedelta
from django.contrib import messages

@login_required
def home(request):
    """Dashboard home view showing overview of student or teacher data"""
    user = request.user
    
    if user.is_student():
        # Student dashboard
        enrolled_courses = user.courses_enrolled.all()
        recent_courses = enrolled_courses.order_by('-updated_at')[:5]
        
        # Get overall progress
        total_content_items = 0
        completed_content_items = 0
        
        for course in enrolled_courses:
            all_content = Content.objects.filter(chapter__course=course)
            total_content_items += all_content.count()
            completed_content_items += StudentProgress.objects.filter(
                student=user, 
                content__in=all_content,
                completed=True
            ).count()
        
        overall_progress = 0
        if total_content_items > 0:
            overall_progress = (completed_content_items / total_content_items) * 100
            
        # Get recent notifications
        notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Get completed courses
        completed_courses = CourseCompletion.objects.filter(student=user).select_related('course')
        
        # Get recent quiz results
        recent_quiz_results = QuizResult.objects.filter(
            student=user
        ).select_related('quiz').order_by('-completed_at')[:5]
        
        # Get assigned quizzes
        assigned_quizzes = QuizAssignment.objects.filter(students=user).select_related('quiz').order_by('due_date')
        # Mark quizzes as completed, pending or overdue
        for assignment in assigned_quizzes:
            if QuizResult.objects.filter(student=user, quiz=assignment.quiz).exists():
                assignment.status = 'completed'
            elif assignment.due_date and assignment.due_date < datetime.now():
                assignment.status = 'overdue'
            else:
                assignment.status = 'pending'
        
        context = {
            'recent_courses': recent_courses,
            'enrolled_courses': enrolled_courses,
            'completed_courses': completed_courses,
            'notifications': notifications,
            'overall_progress': overall_progress,
            'completed_content_items': completed_content_items,
            'total_content_items': total_content_items,
            'recent_quiz_results': recent_quiz_results,
            'assigned_quizzes': assigned_quizzes[:5],  # Afficher les 5 plus récents/urgents
        }
        
        return render(request, 'dashboard/home.html', context)
        
    elif user.is_teacher():
        # Teacher dashboard
        teaching_courses = user.courses_teaching.all()
        student_count = User.objects.filter(courses_enrolled__in=teaching_courses).distinct().count()
        
        # Get notifications - s'assurer que l'enseignant voit les messages des élèves
        notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Most active courses
        courses_with_activity = teaching_courses.annotate(
            progress_count=Count('chapters__contents__student_progress')
        ).order_by('-progress_count')[:5]
        
        # Recent completions
        recent_completions = CourseCompletion.objects.filter(
            course__in=teaching_courses
        ).select_related('student', 'course').order_by('-completion_date')[:10]
        
        # Get quiz statistics
        quiz_count = Quiz.objects.filter(course__in=teaching_courses).count()
        
        # Get recent quizzes
        recent_quizzes = Quiz.objects.filter(
            course__in=teaching_courses
        ).annotate(
            question_count=Count('questions')
        ).select_related('course').order_by('-created_at')[:5]
        
        # Get recent quiz results
        recent_quiz_results = QuizResult.objects.filter(
            quiz__course__in=teaching_courses
        ).select_related('student', 'quiz').order_by('-completed_at')[:5]
        
        context = {
            'teaching_courses': teaching_courses,
            'student_count': student_count,
            'courses_with_activity': courses_with_activity,
            'recent_completions': recent_completions,
            'quiz_count': quiz_count,
            'recent_quizzes': recent_quizzes,
            'recent_quiz_results': recent_quiz_results,
            'notifications': notifications,  # Ajout des notifications pour l'enseignant
        }
        
        return render(request, 'dashboard/teacher_home.html', context)
    
    # Admin view can be added here if needed
    return render(request, 'dashboard/home.html', {})


@login_required
def student_progress(request, course_id=None):
    """View for showing detailed student progress"""
    user = request.user
    
    if course_id:
        course = get_object_or_404(Course, id=course_id)
        chapters = Chapter.objects.filter(course=course).prefetch_related('contents')
        
        # Build a data structure with progress information
        progress_data = []
        
        for chapter in chapters:
            chapter_data = {
                'chapter': chapter,
                'contents': []
            }
            
            for content in chapter.contents.all():
                try:
                    progress = StudentProgress.objects.get(student=user, content=content)
                    completed = progress.completed
                    last_accessed = progress.last_accessed
                    time_spent = progress.time_spent
                except StudentProgress.DoesNotExist:
                    completed = False
                    last_accessed = None
                    time_spent = 0
                
                chapter_data['contents'].append({
                    'content': content,
                    'completed': completed,
                    'last_accessed': last_accessed,
                    'time_spent': time_spent
                })
            
            progress_data.append(chapter_data)
        
        # Calculate overall progress for this course
        total_content = Content.objects.filter(chapter__course=course).count()
        completed_content = StudentProgress.objects.filter(
            student=user,
            content__chapter__course=course,
            completed=True
        ).count()
        
        progress_percentage = 0
        if total_content > 0:
            progress_percentage = (completed_content / total_content) * 100
        
        # Determine progress class based on percentage
        progress_class = ""
        if progress_percentage <= 25:
            progress_class = "progress-low"
        elif progress_percentage <= 50:
            progress_class = "progress-medium-low"
        elif progress_percentage <= 75:
            progress_class = "progress-medium-high"
        else:
            progress_class = "progress-high"
        
        # Get quiz results
        course_quizzes = QuizResult.objects.filter(
            student=user,
            quiz__course=course
        ).select_related('quiz').order_by('quiz__title')
        
        context = {
            'course': course,
            'progress_data': progress_data,
            'progress_percentage': progress_percentage,
            'progress_class': progress_class,
            'completed_content': completed_content,
            'total_content': total_content,
            'course_quizzes': course_quizzes
        }
        
        return render(request, 'dashboard/student_progress.html', context)
    
    # If no course_id specified, show progress overview for all courses
    enrolled_courses = user.courses_enrolled.all()
    courses_progress = []
    
    for course in enrolled_courses:
        total_content = Content.objects.filter(chapter__course=course).count()
        completed_content = StudentProgress.objects.filter(
            student=user,
            content__chapter__course=course,
            completed=True
        ).count()
        
        progress_percentage = 0
        if total_content > 0:
            progress_percentage = (completed_content / total_content) * 100
            
        courses_progress.append({
            'course': course,
            'progress_percentage': progress_percentage,
            'completed_content': completed_content,
            'total_content': total_content
        })
    
    context = {
        'courses_progress': courses_progress
    }
    
    return render(request, 'dashboard/student_progress_overview.html', context)

@login_required
def notifications(request):
    """View all notifications for the current user"""
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    
    # Mark all as read
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        Notification.objects.filter(user=user, read=False).update(read=True)
        return redirect('dashboard:notifications')
    
    context = {
        'notifications': notifications,
        'unread_count': notifications.filter(read=False).count()
    }
    
    return render(request, 'dashboard/notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return redirect('dashboard:notifications')

@login_required
def update_progress(request, content_id):
    """Update progress for a specific content"""
    if request.method == 'POST':
        content = get_object_or_404(Content, id=content_id)
        user = request.user
        
        # Get or create progress record
        progress, created = StudentProgress.objects.get_or_create(
            student=user,
            content=content
        )
        
        # Update progress
        if 'completed' in request.POST:
            progress.completed = True
        
        if 'time_spent' in request.POST:
            try:
                time_spent = int(request.POST['time_spent'])
                progress.time_spent += time_spent
            except ValueError:
                pass
        
        progress.save()
        
        # Check if course is completed
        course = content.chapter.course
        total_content = Content.objects.filter(chapter__course=course).count()
        completed_content = StudentProgress.objects.filter(
            student=user,
            content__chapter__course=course,
            completed=True
        ).count()
        
        # If all content is completed, mark the course as complete
        if total_content > 0 and completed_content == total_content:
            CourseCompletion.objects.get_or_create(
                student=user,
                course=course
            )
        
        # Redirect back to content page or student progress
        return redirect('courses:content_detail', content_id=content_id)
    
    return redirect('dashboard:student_progress')

@login_required
def teacher_course_analytics(request, course_id):
    """Analytics for a specific course (teacher view)"""
    user = request.user
    if not user.is_teacher():
        return redirect('dashboard:home')
    
    course = get_object_or_404(Course, id=course_id, teacher=user)
    
    # Get enrolled students
    students = course.students.all()
    
    # Get completion rate
    total_students = students.count()
    completed_students = CourseCompletion.objects.filter(course=course).count()
    completion_rate = 0
    if total_students > 0:
        completion_rate = (completed_students / total_students) * 100
    
    # Get content engagement
    contents = Content.objects.filter(chapter__course=course)
    content_engagement = []
    
    for content in contents:
        views = StudentProgress.objects.filter(content=content).count()
        completions = StudentProgress.objects.filter(content=content, completed=True).count()
        avg_time = StudentProgress.objects.filter(content=content).aggregate(
            avg_time=Sum('time_spent') / Count('id')
        )['avg_time'] or 0
        
        content_engagement.append({
            'content': content,
            'views': views,
            'completions': completions,
            'avg_time': avg_time
        })
    
    # Get student progress
    student_progress_data = []
    
    for student in students:
        completed_content = StudentProgress.objects.filter(
            student=student,
            content__chapter__course=course,
            completed=True
        ).count()
        
        progress_percentage = 0
        if contents.count() > 0:
            progress_percentage = (completed_content / contents.count()) * 100
            
        student_progress_data.append({
            'student': student,
            'progress_percentage': progress_percentage,
            'completed_content': completed_content,
            'total_content': contents.count()
        })
    
    # Get quiz statistics for this course
    course_quizzes = Quiz.objects.filter(course=course).annotate(
        question_count=Count('questions'),
        completion_count=Count('results', distinct=True)
    )
    
    # Get quiz results for analysis
    quiz_performance = []
    for quiz in course_quizzes:
        results = QuizResult.objects.filter(quiz=quiz)
        avg_score = results.aggregate(avg_score=Sum('score')/Count('id'))['avg_score'] or 0
        max_possible = quiz.question_count  # Assuming 1 point per question as default
        
        quiz_performance.append({
            'quiz': quiz,
            'avg_score': avg_score,
            'max_possible': max_possible,
            'completion_count': quiz.completion_count,
            'completion_rate': (quiz.completion_count / total_students * 100) if total_students > 0 else 0
        })
    
    context = {
        'course': course,
        'total_students': total_students,
        'completed_students': completed_students,
        'completion_rate': completion_rate,
        'content_engagement': content_engagement,
        'student_progress_data': student_progress_data,
        'course_quizzes': course_quizzes,
        'quiz_performance': quiz_performance
    }
    
    return render(request, 'dashboard/teacher_course_analytics.html', context)

@login_required
def contact_student(request, student_id):
    """View for teacher to contact a specific student"""
    user = request.user
    if not user.is_teacher():
        return redirect('dashboard:home')
    
    student = get_object_or_404(User, id=student_id)
    course_id = request.GET.get('course_id')
    
    # Optional: If course_id is provided, verify the student is enrolled in this course
    if course_id:
        course = get_object_or_404(Course, id=course_id, teacher=user)
        if not course.students.filter(id=student_id).exists():
            # Student not enrolled in this course
            return redirect('dashboard:teacher_course_analytics', course_id=course_id)
    
    # Handle form submission for sending message
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            # Create notification for student
            Notification.objects.create(
                user=student,
                title=f"Message from {user.get_full_name() or user.username}",
                message=message,
                notification_type='message'
            )
            # Redirect back with success message
            messages.success(request, "Message sent successfully to student.")
            if course_id:
                return redirect('dashboard:teacher_course_analytics', course_id=course_id)
            return redirect('dashboard:home')
    
    context = {
        'student': student,
        'course_id': course_id
    }
    
    return render(request, 'dashboard/contact_student.html', context)
# dashboard/views.py - Ajouter à la fin du fichier

@login_required
def assign_quiz(request, quiz_id):
    """Assign a quiz to students"""
    user = request.user
    if not user.is_teacher():
        return redirect('dashboard:home')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    # Vérifier que l'enseignant est propriétaire du quiz
    if quiz.course.teacher != user:
        messages.error(request, "Vous n'êtes pas autorisé à assigner ce quiz.")
        return redirect('dashboard:home')
    
    # Récupérer les étudiants inscrits au cours
    students = quiz.course.students.all()
    
    if request.method == 'POST':
        student_ids = request.POST.getlist('students')
        due_date_str = request.POST.get('due_date')
        message = request.POST.get('message', '')
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                messages.error(request, "Format de date invalide")
                return render(request, 'dashboard/assign_quiz.html', {'quiz': quiz, 'students': students})
        
        # Créer l'assignation
        assignment = QuizAssignment.objects.create(
            quiz=quiz,
            assigned_by=user,
            due_date=due_date,
            message=message
        )
        
        # Ajouter les étudiants sélectionnés
        selected_students = User.objects.filter(id__in=student_ids)
        assignment.students.set(selected_students)
        
        # Créer des notifications pour les étudiants
        for student in selected_students:
            notification_message = f"Un nouveau quiz '{quiz.title}' vous a été assigné."
            if message:
                notification_message += f"\nMessage de l'enseignant: {message}"
            if due_date:
                notification_message += f"\nÀ compléter avant le: {due_date.strftime('%d/%m/%Y à %H:%M')}"
                
            Notification.objects.create(
                user=student,
                title=f"Nouveau quiz assigné: {quiz.title}",
                message=notification_message
            )
        
        messages.success(request, f"Quiz assigné à {len(selected_students)} étudiant(s) avec succès.")
        return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    
    context = {
        'quiz': quiz,
        'students': students
    }
    
    return render(request, 'dashboard/assign_quiz.html', context)

@login_required
def assigned_quizzes(request):
    """View assigned quizzes (student view)"""
    user = request.user
    if not user.is_student():
        return redirect('dashboard:home')
    
    # Get all quiz assignments for this student
    assignments = QuizAssignment.objects.filter(students=user).select_related('quiz', 'assigned_by')
    
    # Get completed quiz results
    completed_quizzes = QuizResult.objects.filter(student=user).values_list('quiz_id', flat=True)
    
    # Mark quizzes as completed or pending
    for assignment in assignments:
        assignment.status = 'completed' if assignment.quiz.id in completed_quizzes else 'pending'
        if assignment.due_date and assignment.due_date < datetime.now() and assignment.status == 'pending':
            assignment.status = 'overdue'
    
    context = {
        'assignments': assignments
    }
    
    return render(request, 'dashboard/assigned_quizzes.html', context)
@login_required
def contact_teacher(request, teacher_id):
    """View for student to contact a specific teacher"""
    user = request.user
    if not user.is_student():
        return redirect('dashboard:home')
    
    teacher = get_object_or_404(User, id=teacher_id, role=User.TEACHER)
    course_id = request.GET.get('course_id')
    
    # Optional: If course_id is provided, verify the teacher teaches this course
    if course_id:
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        if not course.students.filter(id=user.id).exists():
            # Student not enrolled in this course
            return redirect('dashboard:home')
    
    # Handle form submission for sending message
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            # Create notification for teacher
            Notification.objects.create(
                user=teacher,
                title=f"Message from student {user.get_full_name() or user.username}",
                message=message,
                notification_type='message'
            )
            # Redirect back with success message
            messages.success(request, "Message sent successfully to teacher.")
            if course_id:
                return redirect('courses:course_detail', course_id=course_id)
            return redirect('dashboard:home')
    
    context = {
        'teacher': teacher,
        'course_id': course_id
    }
    
    return render(request, 'dashboard/contact_teacher.html', context)