from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    """Form for adding and editing comments"""
    
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Écrivez votre commentaire...'
            }),
        }
        labels = {
            'text': 'Commentaire',
        }