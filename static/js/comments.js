document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
    
    // AJAX comment submission
    const commentForms = document.querySelectorAll('.comment-form');
    commentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const url = this.getAttribute('action');
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Create new comment element
                    const commentsList = document.querySelector('.comments-list');
                    const newComment = createCommentElement(data);
                    
                    // Add to the top if it's a main comment
                    if (!formData.get('parent_id')) {
                        if (commentsList.querySelector('.no-comments')) {
                            commentsList.innerHTML = '';
                        }
                        commentsList.insertAdjacentHTML('afterbegin', newComment);
                    } else {
                        // Add reply to parent comment
                        const parentId = formData.get('parent_id');
                        const parentComment = document.getElementById(`comment-${parentId}`);
                        
                        let repliesContainer = parentComment.querySelector('.replies');
                        if (!repliesContainer) {
                            parentComment.insertAdjacentHTML('beforeend', '<div class="replies"></div>');
                            repliesContainer = parentComment.querySelector('.replies');
                        }
                        
                        repliesContainer.insertAdjacentHTML('beforeend', newComment);
                        
                        // Hide reply form
                        document.getElementById(`reply-form-${parentId}`).style.display = 'none';
                    }
                    
                    // Clear form
                    this.reset();
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
    
    // Function to create comment element
    function createCommentElement(data) {
        const isReply = !!data.parent_id;
        const commentClass = isReply ? 'comment comment-reply' : 'comment';
        
        return `
            <div class="${commentClass}" id="comment-${data.comment_id}">
                <div class="comment-header">
                    <div class="comment-user">
                        <img src="/static/images/default-avatar.png" alt="${data.username}" class="avatar-sm">
                        <span class="username">${data.username}</span>
                        <span class="comment-date">${data.created_at}</span>
                    </div>
                    
                    <div class="comment-actions">
                        <div class="comment-votes">
                            <button class="btn-vote upvote" data-comment-id="${data.comment_id}" data-vote-type="up">
                                <i class="fas fa-arrow-up"></i>
                                <span class="upvote-count">0</span>
                            </button>
                            <button class="btn-vote downvote" data-comment-id="${data.comment_id}" data-vote-type="down">
                                <i class="fas fa-arrow-down"></i>
                                <span class="downvote-count">0</span>
                            </button>
                        </div>
                        
                        <button class="btn-reply" data-comment-id="${data.comment_id}">
                            <i class="fas fa-reply"></i> Répondre
                        </button>
                        
                        <div class="dropdown">
                            <button class="btn-more" id="dropdown-${data.comment_id}" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="dropdown-${data.comment_id}">
                                <li><a class="dropdown-item edit-comment" href="#" data-comment-id="${data.comment_id}">
                                    <i class="fas fa-edit"></i> Modifier
                                </a></li>
                                <li><a class="dropdown-item delete-comment" href="#" data-comment-id="${data.comment_id}">
                                    <i class="fas fa-trash"></i> Supprimer
                                </a></li>
                                <li><a class="dropdown-item report-comment" href="#" data-comment-id="${data.comment_id}">
                                    <i class="fas fa-flag"></i> Signaler
                                </a></li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="comment-content">
                    <p>${data.text}</p>
                </div>
                
                <div class="reply-form-container" id="reply-form-${data.comment_id}" style="display: none;">
                    <form class="comment-form reply-form" action="/comments/add/" method="post">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
                        <input type="hidden" name="parent_id" value="${data.comment_id}">
                        <input type="hidden" name="content_id" value="${data.content_id || ''}">
                        <input type="hidden" name="course_id" value="${data.course_id || ''}">
                        <div class="form-group">
                            <textarea name="text" class="form-control" rows="2" placeholder="Votre réponse..." required></textarea>
                        </div>
                        <div class="form-actions">
                            <button type="button" class="btn btn-sm btn-secondary cancel-reply" data-comment-id="${data.comment_id}">
                                Annuler
                            </button>
                            <button type="submit" class="btn btn-sm btn-primary">Répondre</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
    }
    
    // Handle reply button clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-reply') || e.target.closest('.btn-reply')) {
            const button = e.target.classList.contains('btn-reply') ? e.target : e.target.closest('.btn-reply');
            const commentId = button.dataset.commentId;
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            
            // Hide all other reply forms
            document.querySelectorAll('.reply-form-container').forEach(form => {
                if (form.id !== `reply-form-${commentId}`) {
                    form.style.display = 'none';
                }
            });
            
            // Toggle this reply form
            replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
            
            // Focus on textarea
            if (replyForm.style.display === 'block') {
                replyForm.querySelector('textarea').focus();
            }
        }
    });
    
    // Handle cancel reply button clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('cancel-reply')) {
            const commentId = e.target.dataset.commentId;
            document.getElementById(`reply-form-${commentId}`).style.display = 'none';
        }
    });
    
    // Handle voting
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-vote') || e.target.closest('.btn-vote')) {
            e.preventDefault();
            
            const button = e.target.classList.contains('btn-vote') ? e.target : e.target.closest('.btn-vote');
            const commentId = button.dataset.commentId;
            const voteType = button.dataset.voteType;
            
            fetch('/comments/vote/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    comment_id: commentId,
                    vote_type: voteType
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update vote counts
                    const commentEl = document.getElementById(`comment-${commentId}`);
                    commentEl.querySelector('.upvote-count').textContent = data.upvotes;
                    commentEl.querySelector('.downvote-count').textContent = data.downvotes;
                    
                    // Update button states
                    commentEl.querySelectorAll('.btn-vote').forEach(btn => {
                        btn.classList.remove('voted');
                    });
                    
                    if (data.user_vote) {
                        const voteButton = commentEl.querySelector(`.btn-vote[data-vote-type="${data.user_vote}"]`);
                        if (voteButton) {
                            voteButton.classList.add('voted');
                        }
                    }
                }
            })
            .catch(error => console.error('Error:', error));
        }
    });
    
    // Handle comment editing
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('edit-comment') || e.target.closest('.edit-comment')) {
            e.preventDefault();
            
            const link = e.target.classList.contains('edit-comment') ? e.target : e.target.closest('.edit-comment');
            const commentId = link.dataset.commentId;
            const commentEl = document.getElementById(`comment-${commentId}`);
            const commentContent = commentEl.querySelector('.comment-content');
            const commentText = commentContent.querySelector('p').textContent;
            
            // Create edit form
            commentContent.innerHTML = `
                <form class="edit-comment-form" data-comment-id="${commentId}">
                    <div class="form-group">
                        <textarea class="form-control" rows="3" required>${commentText}</textarea>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn btn-sm btn-secondary cancel-edit" data-comment-id="${commentId}">
                            Annuler
                        </button>
                        <button type="submit" class="btn btn-sm btn-primary">Enregistrer</button>
                    </div>
                </form>
            `;
            
            // Focus on textarea
            commentContent.querySelector('textarea').focus();
        }
    });
    
    // Handle cancel edit
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('cancel-edit')) {
            const commentId = e.target.dataset.commentId;
            const commentEl = document.getElementById(`comment-${commentId}`);
            
            fetch(`/comments/${commentId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                commentEl.querySelector('.comment-content').innerHTML = `<p>${data.text}</p>`;
            })
            .catch(error => console.error('Error:', error));
        }
    });
    
    // Handle edit form submission
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('edit-comment-form')) {
            e.preventDefault();
            
            const form = e.target;
            const commentId = form.dataset.commentId;
            const commentEl = document.getElementById(`comment-${commentId}`);
            const newText = form.querySelector('textarea').value;
            
            fetch(`/comments/${commentId}/edit/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    text: newText
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    commentEl.querySelector('.comment-content').innerHTML = `<p>${data.text}</p>`;
                }
            })
            .catch(error => console.error('Error:', error));
        }
    });
    
    // Handle comment deletion
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-comment') || e.target.closest('.delete-comment')) {
            e.preventDefault();
            
            const link = e.target.classList.contains('delete-comment') ? e.target : e.target.closest('.delete-comment');
            const commentId = link.dataset.commentId;
            
            if (confirm('Êtes-vous sûr de vouloir supprimer ce commentaire ?')) {
                fetch(`/comments/${commentId}/delete/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        const commentEl = document.getElementById(`comment-${commentId}`);
                        commentEl.remove();
                        
                        // Check if there are no more comments
                        const commentsList = document.querySelector('.comments-list');
                        if (commentsList && !commentsList.querySelector('.comment')) {
                            commentsList.innerHTML = '<p class="no-comments">Aucun commentaire pour le moment. Soyez le premier à commenter !</p>';
                        }
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        }
    });
    
    // Handle comment reporting
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('report-comment') || e.target.closest('.report-comment')) {
            e.preventDefault();
            
            const link = e.target.classList.contains('report-comment') ? e.target : e.target.closest('.report-comment');
            const commentId = link.dataset.commentId;
            
            // Show report modal
            const reportModal = new bootstrap.Modal(document.getElementById('reportCommentModal'));
            document.getElementById('reportCommentId').value = commentId;
            reportModal.show();
        }
    });
    
    // Submit report form
    const reportForm = document.getElementById('reportCommentForm');
    if (reportForm) {
        reportForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/comments/report/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Close modal
                    bootstrap.Modal.getInstance(document.getElementById('reportCommentModal')).hide();
                    
                    // Show success message
                    const toast = new bootstrap.Toast(document.getElementById('reportSuccessToast'));
                    toast.show();
                    
                    // Reset form
                    reportForm.reset();
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }
});