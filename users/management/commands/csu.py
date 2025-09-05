from django.core.management import BaseCommand
from users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not User.objects.filter(email='admin@example.com').exists():
            user = User.objects.create(
                email='admin@example.com',
                first_name='Admin',
                is_active=True,
                is_staff=True,
                is_superuser=True
            )
            user.set_password('123qwe')
            user.save()
            self.stdout.write(
                self.style.SUCCESS('Суперпользователь создан: admin@example.com / 123qwe')
            )
        else:
            self.stdout.write('Суперпользователь уже существует')
