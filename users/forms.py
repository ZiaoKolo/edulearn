# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserLoginForm(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur", 
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Mot de passe", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Mot de passe', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Votre mot de passe doit contenir au moins 8 caractères et ne peut pas être entièrement numérique."
    )
    password2 = forms.CharField(
        label='Confirmer le mot de passe', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Saisissez le même mot de passe que précédemment, pour vérification."
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'bio', 'profile_pic']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_pic': forms.FileInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'username': "Requis. 150 caractères maximum. Uniquement des lettres, chiffres et @/./+/-/_.",
            'email': "Entrez une adresse email valide.",
            'role': "Sélectionnez votre rôle sur la plateforme.",
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprimer l'option administrateur des choix possibles
        choices = [choice for choice in User.ROLE_CHOICES if choice[0] != User.ADMIN]
        self.fields['role'].choices = choices
    
    def clean_password2(self):
        # Vérifier que les deux mots de passe correspondent
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2
    
    def clean_email(self):
        # Vérifier que l'email n'est pas déjà utilisé
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email
    
    def clean_role(self):
        # Vérification supplémentaire pour empêcher le rôle admin
        role = self.cleaned_data.get('role')
        if role == User.ADMIN:
            raise forms.ValidationError("La création de comptes administrateur n'est pas autorisée.")
        return role
    
    def save(self, commit=True):
        # Sauvegarder le mot de passe fourni en format haché
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'profile_pic', 'bio']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_pic': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        is_admin = kwargs.pop('is_admin', False)
        super(UserProfileForm, self).__init__(*args, **kwargs)
        
        # Si c'est un administrateur qui modifie un profil, permettre de changer le rôle
        if is_admin:
            self.fields['role'] = forms.ChoiceField(
                choices=User.ROLE_CHOICES,
                widget=forms.Select(attrs={'class': 'form-select'}),
                label="Rôle"
            )
            
            # Réorganiser les champs pour inclure le rôle
            self.Meta.fields = ['email', 'first_name', 'last_name', 'role', 'profile_pic', 'bio']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Vérifier que l'email n'est pas déjà utilisé par un autre utilisateur
            users_with_email = User.objects.filter(email=email).exclude(id=self.instance.id)
            if users_with_email.exists():
                raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email
