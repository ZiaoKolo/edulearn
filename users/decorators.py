# users/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

def admin_required(function):
    """
    Décorateur qui vérifie si l'utilisateur est un administrateur.
    Redirige vers la page de connexion si l'utilisateur n'est pas connecté,
    ou affiche un message d'erreur et redirige vers le tableau de bord si l'utilisateur n'est pas admin.
    """
    def check_admin(user):
        if not user.is_authenticated:
            return False
        if not user.is_admin_user():
            return False
        return True
    
    def wrapper(request, *args, **kwargs):
        if check_admin(request.user):
            return function(request, *args, **kwargs)
        elif request.user.is_authenticated:
            messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
            return redirect('dashboard:home')
        else:
            messages.error(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect(f"{reverse('users:login')}?next={request.path}")
    
    return wrapper