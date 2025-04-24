from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Count

from .models import Course, Chapter, Content, Subject
from .forms import CourseForm, ChapterForm, ContentForm, SubjectForm
from dashboard.models import StudentProgress

# Course listing views
def course_list(request):
    subjects = Subject.objects.annotate(total_courses=Count('courses'))
    courses = Course.objects.all()
    
    # Handle search query
    query = request.GET.get('query')
    if query:
        courses = courses.filter(title__icontains=query) | courses.filter(description__icontains=query)
    
    return render(request, 'courses/course_list.html', {
        'subjects': subjects,
        'courses': courses,
        'query': query
    })

def course_list_by_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    courses = Course.objects.filter(subject=subject)
    
    return render(request, 'courses/course_list.html', {
        'subject': subject,
        'courses': courses,
        'subjects': Subject.objects.annotate(total_courses=Count('courses'))
    })

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    chapters = course.chapters.all()
    
    # Check if user is enrolled
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = course.students.filter(id=request.user.id).exists()
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'chapters': chapters,
        'is_enrolled': is_enrolled
    })

# Chapter views
def chapter_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    chapters = course.chapters.all()
    
    # Check if user is enrolled or is the teacher or admin
    if not (request.user.is_authenticated and 
            (course.teacher == request.user or 
             course.students.filter(id=request.user.id).exists() or
             request.user.is_admin_user())):
        return HttpResponseForbidden("You must be enrolled in this course to view its chapters")
    
    return render(request, 'courses/chapter_list.html', {
        'course': course,
        'chapters': chapters
    })

def chapter_detail(request, chapter_id):
    # Ajouter un log pour le débogage
    print(f"Accessing chapter {chapter_id}")
    
    chapter = get_object_or_404(Chapter, id=chapter_id)
    course = chapter.course
    contents = chapter.contents.all()
    
    # Check if user is enrolled or is the teacher or admin
    if not (request.user.is_authenticated and 
            (course.teacher == request.user or 
             course.students.filter(id=request.user.id).exists() or
             request.user.is_admin_user())):
        return HttpResponseForbidden("You must be enrolled in this course to view this chapter")
    
    # Get progress for each content if user is a student
    if request.user.is_authenticated and hasattr(request.user, 'is_student') and request.user.is_student():
        # Instead of creating a dictionary, add the progress directly to each content object
        for content in contents:
            progress, created = StudentProgress.objects.get_or_create(
                student=request.user,
                content=content
            )
            # Add progress as an attribute to the content object
            content.progress = progress
    
    return render(request, 'courses/chapter_detail.html', {
        'chapter': chapter,
        'course': course,
        'contents': contents
        # No need to pass content_progress dictionary anymore
    })

def content_detail(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    chapter = content.chapter
    course = chapter.course
    
    # Check if user is enrolled or is the teacher or admin
    if not (request.user.is_authenticated and 
            (course.teacher == request.user or 
             course.students.filter(id=request.user.id).exists() or
             request.user.is_admin_user())):
        return HttpResponseForbidden("You must be enrolled in this course to view this content")
    
    # Get all contents in the same chapter to add progress
    contents = chapter.contents.all()
    
    # Get the previous and next content
    prev_content = None
    next_content = None
    
    # Get ordered contents to find prev and next
    ordered_contents = list(contents.order_by('order'))
    current_index = None
    
    for i, c in enumerate(ordered_contents):
        if c.id == content.id:
            current_index = i
            break
    
    if current_index is not None:
        if current_index > 0:
            prev_content = ordered_contents[current_index - 1]
        if current_index < len(ordered_contents) - 1:
            next_content = ordered_contents[current_index + 1]
    
    # Update student progress if user is a student
    if request.user.is_authenticated and hasattr(request.user, 'is_student') and request.user.is_student():
        # Update progress for the current content
        progress, created = StudentProgress.objects.get_or_create(
            student=request.user,
            content=content
        )
        
        # Mark as completed when accessed
        if not progress.completed:
            progress.completed = True
            progress.save()
        
        # Add progress to all contents in the chapter for the sidebar
        for c in contents:
            prog, _ = StudentProgress.objects.get_or_create(
                student=request.user,
                content=c
            )
            c.progress = prog
    
    return render(request, 'courses/content_detail.html', {
        'content': content,
        'chapter': chapter,
        'course': course,
        'prev_content': prev_content,
        'next_content': next_content
    })
# Course management views (for teachers)
@login_required
def course_create(request):
    if not hasattr(request.user, 'is_teacher') or not request.user.is_teacher():
        return HttpResponseForbidden("Only teachers can create courses")
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, "Course created successfully!")
            return redirect('courses:course_detail', course_id=course.id)
    else:
        form = CourseForm()
    
    return render(request, 'courses/course_form.html', {
        'form': form,
        'title': 'Create a New Course'
    })

@login_required
def course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if the user is the teacher of this course or admin
    if request.user != course.teacher and not (hasattr(request.user, 'is_admin_user') and request.user.is_admin_user()):
        return HttpResponseForbidden("You don't have permission to edit this course")
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully!")
            return redirect('courses:course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'courses/course_form.html', {
        'form': form,
        'course': course,
        'title': 'Edit Course'
    })

@login_required
def course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if the user is the teacher of this course or admin
    if request.user != course.teacher and not (hasattr(request.user, 'is_admin_user') and request.user.is_admin_user()):
        return HttpResponseForbidden("You don't have permission to delete this course")
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, "Course deleted successfully!")
        return redirect('courses:course_list')
    
    return render(request, 'courses/course_confirm_delete.html', {
        'course': course
    })

# Chapter management views
@login_required
def chapter_create(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if the user is the teacher of this course or admin
    if request.user != course.teacher and not (hasattr(request.user, 'is_admin_user') and request.user.is_admin_user()):
        return HttpResponseForbidden("You don't have permission to add chapters to this course")
    
    if request.method == 'POST':
        form = ChapterForm(request.POST)
        if form.is_valid():
            chapter = form.save(commit=False)
            chapter.course = course
            
            # Set order to be the next number after the highest existing chapter
            max_order = course.chapters.order_by('-order').first()
            if max_order:
                chapter.order = max_order.order + 1
            else:
                chapter.order = 1
                
            chapter.save()
            messages.success(request, "Chapter created successfully!")
            return redirect('courses:chapter_detail', chapter_id=chapter.id)
    else:
        form = ChapterForm()
    
    return render(request, 'courses/chapter_form.html', {
        'form': form,
        'course': course,
        'title': 'Create a New Chapter'
    })

@login_required
def chapter_edit(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    course = chapter.course
    
    # Check if the user is the teacher of this course or admin
    if request.user != course.teacher and not (hasattr(request.user, 'is_admin_user') and request.user.is_admin_user()):
        return HttpResponseForbidden("You don't have permission to edit this chapter")
    
    if request.method == 'POST':
        form = ChapterForm(request.POST, instance=chapter)
        if form.is_valid():
            form.save()
            messages.success(request, "Chapter updated successfully!")
            return redirect('courses:chapter_detail', chapter_id=chapter.id)
    else:
        form = ChapterForm(instance=chapter)
    
    return render(request, 'courses/chapter_form.html', {
        'form': form,
        'chapter': chapter,
        'course': course,
        'title': 'Edit Chapter'
    })

@login_required
def chapter_delete(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    course = chapter.course
    
    # Check if the user is the teacher of this course or admin
    if request.user != course.teacher and not (hasattr(request.user, 'is_admin_user') and request.user.is_admin_user()):
        return HttpResponseForbidden("You don't have permission to delete this chapter")
    
    if request.method == 'POST':
        chapter.delete()
        messages.success(request, "Chapter deleted successfully!")
        return redirect('courses:course_detail', course_id=course.id)
    
    return render(request, 'courses/chapter_confirm_delete.html', {
        'chapter': chapter,
        'course': course
    })

# Content management views
@login_required
def content_create(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    course = chapter.course
    
    # Check if the user is the teacher of this course or admin
    if request.user != course.teacher and not (hasattr(request.user, 'is_admin_user') and request.user.is_admin_user()):
        return HttpResponseForbidden("You don't have permission to add content to this chapter")
    
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.save(commit=False)
            content.chapter = chapter
            
            # Set order to be the next number after the highest existing content
            max_order = chapter.contents.order_by('-order').first()
            if max_order:
                content.order = max_order.order + 1
            else:
                content.order = 1
                
            content.save()
            messages.success(request, "Content created successfully!")
            return redirect('courses:content_detail', content_id=content.id)
    else:
        form = ContentForm()
    
    return render(request, 'courses/content_form.html', {
        'form': form,
        'chapter': chapter,
        'course': course,
        'title': 'Create New Content'
    })

@login_required
def content_edit(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    chapter = content.chapter
    course = chapter.course
    
    # Check if the user is the teacher of this course or admin
    if request.user != course.teacher and not (hasattr(request.user, 'is_admin_user') and request.user.is_admin_user()):
        return HttpResponseForbidden("You don't have permission to edit this content")
    
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            messages.success(request, "Content updated successfully!")
            return redirect('courses:content_detail', content_id=content.id)
    else:
        form = ContentForm(instance=content)
    
    return render(request, 'courses/content_form.html', {
        'form': form,
        'content': content,
        'chapter': chapter,
        'course': course,
        'title': 'Edit Content'
    })

@login_required
def content_delete(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    chapter = content.chapter
    course = chapter.course
    
    # Check if the user is the teacher of this course or admin
    if request.user != course.teacher and not (hasattr(request.user, 'is_admin_user') and request.user.is_admin_user()):
        return HttpResponseForbidden("You don't have permission to delete this content")
    
    if request.method == 'POST':
        content.delete()
        messages.success(request, "Content deleted successfully!")
        return redirect('courses:chapter_detail', chapter_id=chapter.id)
    
    return render(request, 'courses/content_confirm_delete.html', {
        'content': content,
        'chapter': chapter,
        'course': course
    })

# Enrollment views
@login_required
def course_enroll(request, course_id):
    if not hasattr(request.user, 'is_student') or not request.user.is_student():
        return HttpResponseForbidden("Only students can enroll in courses")
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        # Add student to the course
        course.students.add(request.user)
        messages.success(request, f"You are now enrolled in {course.title}")
        return redirect('courses:course_detail', course_id=course.id)
    
    return render(request, 'courses/course_enroll_confirm.html', {
        'course': course
    })

@login_required
def course_unenroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        # Remove student from the course
        course.students.remove(request.user)
        messages.success(request, f"You have been unenrolled from {course.title}")
        return redirect('courses:course_list')
    
    return render(request, 'courses/course_unenroll_confirm.html', {
        'course': course
    })

# Subject management views (for admins)
@login_required
def subject_list(request):
    if not hasattr(request.user, 'is_admin_user') or not request.user.is_admin_user():
        return HttpResponseForbidden("Only administrators can manage subjects")
    
    subjects = Subject.objects.annotate(total_courses=Count('courses'))
    return render(request, 'courses/subject_list.html', {
        'subjects': subjects
    })

@login_required
def subject_create(request):
    if not hasattr(request.user, 'is_admin_user') or not request.user.is_admin_user():
        return HttpResponseForbidden("Only administrators can create subjects")
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject created successfully!")
            return redirect('courses:subject_list')
    else:
        form = SubjectForm()
    
    return render(request, 'courses/subject_form.html', {
        'form': form,
        'title': 'Create a New Subject'
    })

@login_required
def subject_edit(request, subject_id):
    if not hasattr(request.user, 'is_admin_user') or not request.user.is_admin_user():
        return HttpResponseForbidden("Only administrators can edit subjects")
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject updated successfully!")
            return redirect('courses:subject_list')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'courses/subject_form.html', {
        'form': form,
        'subject': subject,
        'title': 'Edit Subject'
    })

@login_required
def subject_delete(request, subject_id):
    if not hasattr(request.user, 'is_admin_user') or not request.user.is_admin_user():
        return HttpResponseForbidden("Only administrators can delete subjects")
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        subject.delete()
        messages.success(request, "Subject deleted successfully!")
        return redirect('courses:subject_list')
    
    return render(request, 'courses/subject_confirm_delete.html', {
        'subject': subject
    })