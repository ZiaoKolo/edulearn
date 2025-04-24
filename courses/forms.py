from django import forms
from .models import Course, Chapter, Content, Subject

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'subject', 'description', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }

class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ['title', 'order']
        widgets = {
            'order': forms.NumberInput(attrs={'min': 1}),
        }

class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['title', 'content_type', 'text_content', 'file', 'order']
        widgets = {
            'text_content': forms.Textarea(attrs={'rows': 10}),
            'order': forms.NumberInput(attrs={'min': 1}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields conditionally required based on content_type
        self.fields['text_content'].required = False
        self.fields['file'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        text_content = cleaned_data.get('text_content')
        file = cleaned_data.get('file')
        
        # Validate based on content type
        if content_type == 'text' and not text_content:
            self.add_error('text_content', 'Text content is required for text type content.')
        
        if content_type in ['video', 'pdf', 'image'] and not file:
            self.add_error('file', f'File is required for {content_type} type content.')
        
        return cleaned_data