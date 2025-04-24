from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages

from .models import Comment, CommentVote
from .forms import CommentForm
from courses.models import Course, Content

@login_required
def add_comment(request, content_type, object_id):
    """
    Add a new comment to either a course or content.
    content_type can be 'course' or 'content'
    """
    if content_type == 'course':
        related_object = get_object_or_404(Course, id=object_id)
        content_obj = None
        course_obj = related_object
    elif content_type == 'content':
        related_object = get_object_or_404(Content, id=object_id)
        content_obj = related_object
        course_obj = related_object.chapter.course
    else:
        messages.error(request, "Type de commentaire invalide.")
        return redirect('home')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            
            # Check if it's a reply to another comment
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = get_object_or_404(Comment, id=parent_id)
            
            # Set appropriate relationships
            if content_type == 'course':
                comment.course = course_obj
            else:
                comment.content = content_obj
                comment.course = course_obj
            
            comment.save()
            
            # For AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'comment_id': comment.id,
                    'username': comment.user.username,
                    'text': comment.text,
                    'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M'),
                })
            
            # Redirect back to the referring page
            return redirect(request.META.get('HTTP_REFERER', reverse('home')))
    
    else:
        form = CommentForm()
    
    context = {
        'form': form,
        'object': related_object,
        'content_type': content_type,
    }
    
    return render(request, 'comments/add_comment.html', context)

@login_required
def edit_comment(request, comment_id):
    """Edit an existing comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Check if user is the author of the comment
    if request.user != comment.user:
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce commentaire.")
        return redirect('home')
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            
            # For AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'text': comment.text,
                })
            
            return redirect(request.META.get('HTTP_REFERER', reverse('home')))
    else:
        form = CommentForm(instance=comment)
    
    context = {
        'form': form,
        'comment': comment,
    }
    
    return render(request, 'comments/edit_comment.html', context)

@login_required
def delete_comment(request, comment_id):
    """Delete a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Check if user is the author of the comment
    if request.user != comment.user and not request.user.is_admin_user():
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce commentaire.")
        return redirect('home')
    
    if request.method == 'POST':
        comment.delete()
        
        # For AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        messages.success(request, "Commentaire supprimé avec succès.")
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))
    
    context = {
        'comment': comment,
    }
    
    return render(request, 'comments/delete_comment.html', context)

@login_required
def vote_comment(request, comment_id):
    """Upvote or downvote a comment"""
    if request.method != 'POST' or not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    
    comment = get_object_or_404(Comment, id=comment_id)
    vote_type = request.POST.get('vote_type')
    
    if vote_type not in [CommentVote.UPVOTE, CommentVote.DOWNVOTE]:
        return JsonResponse({'status': 'error', 'message': 'Invalid vote type'}, status=400)
    
    # Check if user has already voted
    try:
        vote = CommentVote.objects.get(comment=comment, user=request.user)
        
        # If same vote type, remove the vote (toggle)
        if vote.vote_type == vote_type:
            vote.delete()
            action = 'removed'
        else:
            # Change vote type
            vote.vote_type = vote_type
            vote.save()
            action = 'changed'
            
    except CommentVote.DoesNotExist:
        # Create new vote
        CommentVote.objects.create(
            comment=comment,
            user=request.user,
            vote_type=vote_type
        )
        action = 'added'
    
    # Count votes
    upvotes = CommentVote.objects.filter(comment=comment, vote_type=CommentVote.UPVOTE).count()
    downvotes = CommentVote.objects.filter(comment=comment, vote_type=CommentVote.DOWNVOTE).count()
    
    return JsonResponse({
        'status': 'success',
        'action': action,
        'upvotes': upvotes,
        'downvotes': downvotes
    })

def list_comments(request, content_type, object_id):
    """List all comments for a specific course or content"""
    if content_type == 'course':
        related_object = get_object_or_404(Course, id=object_id)
        comments = Comment.objects.filter(course=related_object, parent=None)
        title = f"Commentaires pour le cours: {related_object.title}"
    elif content_type == 'content':
        related_object = get_object_or_404(Content, id=object_id)
        comments = Comment.objects.filter(content=related_object, parent=None)
        title = f"Commentaires pour: {related_object.title}"
    else:
        messages.error(request, "Type de commentaire invalide.")
        return redirect('home')
    
    context = {
        'comments': comments,
        'object': related_object,
        'content_type': content_type,
        'title': title,
    }
    
    return render(request, 'comments/list_comments.html', context)
