# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .models import User
from .forms import UserLoginForm, UserRegistrationForm, UserProfileForm
from .decorators import admin_required

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                # Rediriger en fonction du rôle de l'utilisateur
                if user.is_admin_user():
                    return redirect('dashboard:home')  # Admin utilise le même tableau de bord
                elif user.is_teacher():
                    return redirect('dashboard:home')  # Vue du professeur dans le tableau de bord
                else:  # Étudiant
                    return redirect('dashboard:home')  # Vue de l'étudiant par défaut
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect('users:login')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Vérification supplémentaire pour le rôle administrateur
            if form.cleaned_data.get('role') == User.ADMIN:
                messages.error(request, "La création de comptes administrateur n'est pas autorisée.")
                return redirect('users:register')
                
            user = form.save()  # Le hashage du mot de passe est géré dans la méthode save() du formulaire
            messages.success(request, "Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.")
            return redirect('users:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_view(request):
    # Récupérer les cours si l'utilisateur est un étudiant ou un enseignant
    context = {'user': request.user}
    
    if request.user.is_student():
        enrolled_courses = request.user.courses_enrolled.all()
        
        # Ajouter les dates d'inscription pour chaque cours
        enrollment_dates = {}
        for course in enrolled_courses:
            try:
                enrollment = course.students.through.objects.get(user=request.user, course=course)
                # Remplacez 'date_joined' par le nom réel du champ date dans votre modèle
                enrollment_dates[course.id] = enrollment.date_joined  
            except Exception:
                enrollment_dates[course.id] = None
        
        context['enrolled_courses'] = enrolled_courses
        context['enrollment_dates'] = enrollment_dates
        
    elif request.user.is_teacher():
        context['teaching_courses'] = request.user.courses_teaching.all()
    
    return render(request, 'users/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Maintenir la session de l'utilisateur après le changement de mot de passe
            update_session_auth_hash(request, user)
            messages.success(request, 'Votre mot de passe a été mis à jour avec succès.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'users/edit_profile.html', {'form': form})

# Vues réservées aux administrateurs
@admin_required
def user_list(request):
    users = User.objects.all().order_by('username')
    
    # Filtrer par rôle si spécifié
    role_filter = request.GET.get('role')
    if role_filter and role_filter in [User.STUDENT, User.TEACHER, User.ADMIN]:
        users = users.filter(role=role_filter)
    
    return render(request, 'users/user_list.html', {
        'users': users,
        'current_filter': role_filter
    })

@admin_required
def user_detail(request, user_id):
    user_profile = get_object_or_404(User, id=user_id)
    
    context = {
        'user_profile': user_profile
    }
    
    # Ajouter des données spécifiques au rôle
    if user_profile.is_student():
        enrolled_courses = user_profile.courses_enrolled.all()
        
        # Ajouter les dates d'inscription pour chaque cours
        enrollment_dates = {}
        for course in enrolled_courses:
            try:
                enrollment = course.students.through.objects.get(user=user_profile, course=course)
                # Utilisez le bon nom de champ pour la date
                enrollment_dates[course.id] = enrollment.date_joined
            except Exception:
                enrollment_dates[course.id] = None
        
        context['enrolled_courses'] = enrolled_courses
        context['enrollment_dates'] = enrollment_dates
        context['quiz_results'] = user_profile.quiz_results.all()
        
    elif user_profile.is_teacher():
        context['teaching_courses'] = user_profile.courses_teaching.all()
    
    return render(request, 'users/user_detail.html', context)

@admin_required
def admin_edit_user(request, user_id):
    user_profile = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Pour les administrateurs, permettre également de modifier le rôle
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile, is_admin=True)
        if form.is_valid():
            form.save()
            messages.success(request, "Le profil de l'utilisateur a été mis à jour avec succès.")
            return redirect('users:user_detail', user_id=user_profile.id)
    else:
        form = UserProfileForm(instance=user_profile, is_admin=True)
    
    return render(request, 'users/admin_edit_user.html', {
        'form': form, 
        'user_profile': user_profile
    })

@admin_required
def delete_user(request, user_id):
    user_profile = get_object_or_404(User, id=user_id)
    
    # Empêcher la suppression de son propre compte
    if user_profile.id == request.user.id:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('users:user_list')
    
    if request.method == 'POST':
        username = user_profile.username
        user_profile.delete()
        messages.success(request, f"L'utilisateur {username} a été supprimé avec succès.")
        return redirect('users:user_list')
    
    return render(request, 'users/confirm_delete.html', {'user_profile': user_profile})

# users/management/commands/createsuperadmin.py
from django.core.management.base import BaseCommand
from users.models import User

class Command(BaseCommand):
    help = 'Crée un utilisateur administrateur'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nom d\'utilisateur')
        parser.add_argument('email', type=str, help='Email')
        parser.add_argument('password', type=str, help='Mot de passe')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        email = kwargs['email']
        password = kwargs['password']

        if not User.objects.filter(username=username).exists():
            admin_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True
            )
            admin_user.role = User.ADMIN
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Administrateur {username} créé avec succès'))
        else:
            self.stdout.write(self.style.ERROR(f'L\'utilisateur {username} existe déjà'))
