from django.contrib import admin
from .models import Comment,CommentVote

admin.site.register(Comment)
admin.site.register(CommentVote)
# Register your models here.
