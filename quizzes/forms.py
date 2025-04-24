from django import forms
from django.forms import inlineformset_factory
from .models import Quiz, Question, Choice, QuizAnswer

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'chapter', 'description', 'time_limit']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'points']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Create a formset for choices
ChoiceFormSet = inlineformset_factory(
    Question, 
    Choice,
    form=ChoiceForm,
    extra=4,
    can_delete=True
)

class TextAnswerForm(forms.Form):
    """Form for text answer questions"""
    answer = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), required=True)