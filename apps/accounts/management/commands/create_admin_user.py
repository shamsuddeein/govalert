import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Create or promote an admin user with is_staff=True and is_superuser=True."

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the admin user.',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email address for the admin user.',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')

        while not username:
            username = input('Username: ').strip()

        while not email:
            email = input('Email address: ').strip()

        # Prompt for password securely
        password = None
        while not password:
            pwd1 = getpass.getpass('Password: ')
            pwd2 = getpass.getpass('Password (again): ')
            if not pwd1:
                self.stdout.write(self.style.ERROR('Password cannot be blank.'))
                continue
            if pwd1 != pwd2:
                self.stdout.write(self.style.ERROR('Passwords do not match. Please try again.'))
                continue
            password = pwd1

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )

        if not created:
            if email and user.email != email:
                user.email = email
            self.stdout.write(f"Updating existing user '{username}'...")
        else:
            self.stdout.write(f"Creating new admin user '{username}'...")

        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully {action} admin user '{username}' (email: {user.email}) with is_staff=True and is_superuser=True."
            )
        )
