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