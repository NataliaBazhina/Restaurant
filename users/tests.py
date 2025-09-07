from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from users.forms import UserRegisterForm, UserUpdateForm, UserChangePasswordForm


class UserModelTest(TestCase):
    """Тесты модели User"""

    def test_create_user(self):
        """Тест создания пользователя"""
        user = User.objects.create(
            email='test@example.com',
            password='testpass123',
            first_name='Иван',
            last_name='Петров'
        )
        user.set_password('testpass123')
        user.save()
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Иван')
        self.assertTrue(user.check_password('testpass123'))

    def test_unique_email(self):
        """Тест уникальности email"""
        User.objects.create(email='test@example.com', password='testpass123')

        with self.assertRaises(Exception):
            User.objects.create(email='test@example.com', password='testpass123')

    def test_get_reservations_count(self):
        """Тест подсчета бронирований"""
        user = User.objects.create(email='test@example.com', password='testpass123')
        user.set_password('testpass123')
        user.save()
        self.assertEqual(user.get_reservations_count(), 0)

    def test_string_representation(self):
        """Тест строкового представления"""
        user = User.objects.create(email='test@example.com', password='testpass123')
        user.set_password('testpass123')
        user.save()
        self.assertEqual(str(user), 'test@example.com')


class UserFormsTest(TestCase):
    """Тесты форм"""

    def test_valid_registration_form(self):
        """Тест валидной формы регистрации"""
        form_data = {
            'email': 'test@example.com',
            'first_name': 'Иван',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_duplicate_email_form(self):
        """Тест дубликата email в форме"""
        User.objects.create(email='test@example.com', password='testpass123')

        form_data = {
            'email': 'test@example.com',
            'first_name': 'Иван',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_password_mismatch_form(self):
        """Тест несовпадения паролей"""
        form_data = {
            'email': 'test@example.com',
            'first_name': 'Иван',
            'password1': 'testpass123',
            'password2': 'differentpass'
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_valid_update_form(self):
        """Тест валидной формы обновления"""
        user = User.objects.create(email='test@example.com', password='testpass123')
        user.set_password('testpass123')
        user.save()

        form_data = {
            'email': 'new@example.com',
            'first_name': 'НовоеИмя'
        }
        form = UserUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())


class UserViewsTest(TestCase):
    """Тесты views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            email='test@example.com',
            first_name='Иван'
        )
        self.user.set_password('testpass123')
        self.user.save()

    def test_user_registration_view(self):
        """Тест регистрации пользователя"""
        self.client.post(reverse('users:register'), {
            'email': 'newuser@example.com',
            'first_name': 'Петр',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_user_login_view(self):
        """Тест входа пользователя"""
        response = self.client.post(reverse('users:login'), {
            'username': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_user_login_invalid_view(self):
        """Тест неуспешного входа"""
        response = self.client.post(reverse('users:login'), {
            'username': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)


class EmailVerificationTest(TestCase):
    """Тесты подтверждения email"""

    def setUp(self):
        self.user = User.objects.create(
            email='test@example.com',
            is_active=False
        )
        self.user.token = 'test-token-123'
        self.user.set_password('testpass123')
        self.user.save()

    def test_email_verification_success(self):
        """Тест успешного подтверждения email"""
        self.client.get(reverse('users:email-confirm', kwargs={'token': 'test-token-123'}))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_email_verification_invalid_token(self):
        """Тест невалидного токена"""
        response = self.client.get(reverse('users:email-confirm', kwargs={'token': 'invalid-token'}))
        self.assertEqual(response.status_code, 404)


class UserAccessTest(TestCase):
    """Тесты доступа к страницам"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            email='user@example.com'
        )
        self.user.set_password('testpass123')
        self.user.save()

        self.admin = User.objects.create(
            email='admin@example.com',
            is_staff=True
        )
        self.admin.set_password('adminpass123')
        self.admin.save()

    def test_user_list_access_denied(self):
        """Тест: обычный пользователь не может видеть список пользователей"""
        self.client.login(email='user@example.com', password='testpass123')
        response = self.client.get(reverse('users:users_list'))
        self.assertNotEqual(response.status_code, 200)

    def test_user_list_access_allowed(self):
        """Тест: администратор может видеть список пользователей"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('users:users_list'))
        self.assertEqual(response.status_code, 200)


class PasswordRecoveryTest(TestCase):
    """Тесты восстановления пароля"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            email='test@example.com',
            first_name='Иван',
            is_active=True
        )
        self.user.set_password('oldpassword123')
        self.user.save()

    def test_password_recovery_form_valid(self):
        """Тест валидной формы восстановления пароля"""
        form_data = {
            'email': 'test@example.com',
            'need_generate': True
        }
        form = UserChangePasswordForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_recovery_form_invalid_email(self):
        """Тест невалидного email в форме"""
        form_data = {
            'email': 'invalid-email',
            'need_generate': True
        }
        form = UserChangePasswordForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_password_recovery_view_get(self):
        """Тест GET запроса к странице восстановления пароля"""
        response = self.client.get(reverse('users:change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], UserChangePasswordForm)

    def test_password_recovery_view_post_valid(self):
        """Тест POST запроса с валидными данными"""
        self.client.post(reverse('users:change_password'), {
            'email': 'test@example.com',
            'need_generate': True
        })
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password('oldpassword123'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn('Новый пароль', mail.outbox[0].subject)

    def test_password_recovery_view_post_invalid_email(self):
        """Тест POST запроса с несуществующим email"""
        response = self.client.post(reverse('users:change_password'), {
            'email': 'nonexistent@example.com',
            'need_generate': True
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], UserChangePasswordForm)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_recovery_view_post_inactive_user(self):
        """Тест восстановления пароля для неактивного пользователя"""
        User.objects.create(
            email='inactive@example.com',
            is_active=False
        )
        self.client.post(reverse('users:change_password'), {
            'email': 'inactive@example.com',
            'need_generate': True
        })
        self.assertEqual(len(mail.outbox), 0)

    def test_email_content_contains_password(self):
        """Тест что email содержит новый пароль"""
        self.client.post(reverse('users:change_password'), {
            'email': 'test@example.com',
            'need_generate': True
        })
        self.assertEqual(len(mail.outbox), 1)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password('oldpassword123'))


class CreateSuperuserCommandTest(TestCase):
    """Тесты для кастомной команды создания суперпользователя"""

    def test_command_output_new_user(self):
        """Тест вывода команды при создании нового пользователя"""
        User.objects.filter(email='admin@example.com').delete()

        out = StringIO()
        call_command('csu', stdout=out)
        output = out.getvalue()
        self.assertIn('Суперпользователь создан', output)
        self.assertIn('admin@example.com', output)

    def test_command_output_existing_user(self):
        """Тест вывода команды при существующем пользователе"""
        call_command('csu')

        out = StringIO()
        call_command('csu', stdout=out)
        output = out.getvalue()
        self.assertIn('Суперпользователь уже существует', output)

    def test_superuser_created(self):
        """Тест создания суперпользователя"""
        User.objects.filter(email='admin@example.com').delete()

        call_command('csu')

        user = User.objects.get(email='admin@example.com')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password('123qwe'))

    def test_superuser_attributes(self):
        """Тест атрибутов суперпользователя"""
        User.objects.filter(email='admin@example.com').delete()

        call_command('csu')

        user = User.objects.get(email='admin@example.com')
        self.assertEqual(user.first_name, 'Admin')
        self.assertEqual(user.email, 'admin@example.com')

    def test_password_verification(self):
        """Тест что пароль работает"""
        User.objects.filter(email='admin@example.com').delete()

        call_command('csu')

        user = User.objects.get(email='admin@example.com')
        self.assertTrue(user.check_password('123qwe'))
        self.assertFalse(user.check_password('wrongpassword'))
