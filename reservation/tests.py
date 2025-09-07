import os
from django.test import TestCase, Client, override_settings
from django.core.exceptions import ValidationError
from django.core import mail
from unittest.mock import Mock, patch
from reservation.tasks import send_reservation_reminders
from reservation.forms import ReservationForm
from reservation.validators import ReservationValidator
from reservation.models import Hall, Table, Reservation
from users.models import User
from django.utils import timezone
from datetime import date, timedelta, time
from django.urls import reverse
from io import StringIO
from django.core.management import call_command


class ValidateGuestsCountTest(TestCase):
    """Тесты для validate_guests_count"""

    def setUp(self):
        self.hall = Hall.objects.create(name="Test Hall")
        self.table = Table.objects.create(
            hall=self.hall,
            number="A1",
            capacity=4,
            x_position=1,
            y_position=1,
            is_active=True
        )

    def test_validate_guests_count_none(self):
        """Тест: количество гостей None"""
        reservation = Mock()
        reservation.guests_count = None
        reservation.table = self.table

        with self.assertRaises(ValidationError) as context:
            ReservationValidator.validate_guests_count(reservation)

        self.assertEqual(context.exception.code, 'guests_count')
        self.assertIn('обязательно для заполнения', str(context.exception))

    def test_validate_guests_count_less_than_1(self):
        """Тест: количество гостей меньше 1"""
        reservation = Mock()
        reservation.guests_count = 0
        reservation.table = self.table

        with self.assertRaises(ValidationError) as context:
            ReservationValidator.validate_guests_count(reservation)

        self.assertEqual(context.exception.code, 'guests_count')
        self.assertIn('не менее 1', str(context.exception))

    def test_validate_guests_count_exceeds_capacity(self):
        """Тест: количество гостей превышает вместимость"""
        reservation = Mock()
        reservation.guests_count = 5
        reservation.table = self.table

        with self.assertRaises(ValidationError) as context:
            ReservationValidator.validate_guests_count(reservation)

        self.assertEqual(context.exception.code, 'guests_count')
        self.assertIn('превышает вместимость', str(context.exception))

    def test_validate_guests_count_valid(self):
        """Тест: валидное количество гостей"""
        reservation = Mock()
        reservation.guests_count = 3
        reservation.table = self.table

        try:
            ReservationValidator.validate_guests_count(reservation)
        except ValidationError:
            self.fail("Валидатор вызвал исключение для валидных данных")

    def test_validate_guests_count_no_table(self):
        """Тест: количество гостей без столика"""
        reservation = Mock()
        reservation.guests_count = 3
        reservation.table = None

        try:
            ReservationValidator.validate_guests_count(reservation)
        except ValidationError:
            self.fail("Валидатор вызвал исключение при отсутствии столика")


class ValidateDateNotInPastTest(TestCase):
    """Тесты для validate_date_not_in_past"""

    def test_validate_date_not_in_past_none(self):
        """Тест: дата None"""
        with self.assertRaises(ValidationError) as context:
            ReservationValidator.validate_date_not_in_past(None)

        self.assertEqual(context.exception.code, 'date')
        self.assertIn('обязательна для заполнения', str(context.exception))

    def test_validate_date_not_in_past_yesterday(self):
        """Тест: дата в прошлом"""
        yesterday = timezone.now().date() - timedelta(days=1)

        with self.assertRaises(ValidationError) as context:
            ReservationValidator.validate_date_not_in_past(yesterday)

        self.assertEqual(context.exception.code, 'date')
        self.assertIn('прошедшую дату', str(context.exception))

    def test_validate_date_not_in_past_today(self):
        """Тест: сегодняшняя дата"""
        today = timezone.now().date()

        try:
            ReservationValidator.validate_date_not_in_past(today)
        except ValidationError:
            self.fail("Валидатор вызвал исключение для сегодняшней даты")

    def test_validate_date_not_in_past_tomorrow(self):
        """Тест: будущая дата"""
        tomorrow = timezone.now().date() + timedelta(days=1)

        try:
            ReservationValidator.validate_date_not_in_past(tomorrow)
        except ValidationError:
            self.fail("Валидатор вызвал исключение для будущей даты")


class ValidateWorkingHoursTest(TestCase):
    """Тесты для validate_working_hours"""

    def test_validate_working_hours_none(self):
        """Тест: время None"""
        with self.assertRaises(ValidationError) as context:
            ReservationValidator.validate_working_hours(None)
        self.assertEqual(context.exception.code, 'start_time')

    def test_validate_working_hours_too_early(self):
        """Тест: слишком раннее время (9:59)"""
        with self.assertRaises(ValidationError) as context:
            ReservationValidator.validate_working_hours(time(9, 59))
        self.assertEqual(context.exception.code, 'start_time')

    def test_validate_working_hours_valid_times(self):
        """Тест: валидное время (10:00 - 22:00)"""
        valid_times = [time(10, 0), time(15, 30), time(22, 0)]
        for valid_time in valid_times:
            try:
                ReservationValidator.validate_working_hours(valid_time)
            except ValidationError:
                self.fail(f"Валидатор вызвал исключение для валидного времени {valid_time}")

    def test_validate_working_hours_too_late(self):
        """Тест: слишком позднее время (22:01 - 23:00)"""
        invalid_times = [time(22, 1), time(22, 30), time(23, 0)]
        for invalid_time in invalid_times:
            with self.assertRaises(ValidationError) as context:
                ReservationValidator.validate_working_hours(invalid_time)
            self.assertEqual(context.exception.code, 'start_time')


class ValidateAvailabilityTest(TestCase):
    """Тесты для validate_availability"""

    def setUp(self):
        self.hall = Hall.objects.create(name="Test Hall")
        self.table = Table.objects.create(
            hall=self.hall,
            number="A1",
            capacity=4,
            x_position=1,
            y_position=1,
            is_active=True
        )
        self.user = User.objects.create(email='test@example.com')
        self.user.set_password('testpass123')
        self.user.save()

    def test_validate_availability_no_conflict_real_db(self):
        """Тест: нет конфликта бронирований (реальная БД)"""

        Reservation.objects.create(
            table=self.table,
            date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            duration=timedelta(hours=2),
            guests_count=2,
            status='confirmed',
            user=self.user
        )
        reservation = Mock()
        reservation.table = self.table
        reservation.date = date.today()
        reservation.start_time = time(14, 0)
        reservation.duration = timedelta(hours=2)
        reservation.status = 'confirmed'
        reservation.pk = None

        try:
            result = ReservationValidator.validate_availability(reservation)
            self.assertTrue(result)
        except ValidationError:
            self.fail("Валидатор вызвал исключение при отсутствии конфликта")

    def test_validate_availability_conflict_real_db(self):
        """Тест: есть конфликт бронирований (реальная БД)"""

        Reservation.objects.create(
            table=self.table,
            date=date.today(),
            start_time=time(15, 0),
            duration=timedelta(hours=2),
            guests_count=2,
            status='confirmed',
            user=self.user
        )
        reservation = Mock()
        reservation.table = self.table
        reservation.date = date.today()
        reservation.start_time = time(16, 0)
        reservation.duration = timedelta(hours=2)
        reservation.status = 'confirmed'
        reservation.pk = None

        with self.assertRaises(ValidationError) as context:
            ReservationValidator.validate_availability(reservation)

        self.assertEqual(context.exception.code, 'table')
        self.assertIn('забронирован', str(context.exception))

    def test_validate_availability_canceled_status(self):
        """Тест: отмененное бронирование не проверяется"""
        reservation = Mock()
        reservation.status = 'canceled'
        reservation.table = None

        try:
            result = ReservationValidator.validate_availability(reservation)
            self.assertTrue(result)
        except ValidationError:
            self.fail("Валидатор вызвал исключение для отмененного бронирования")

    def test_validate_availability_missing_data(self):
        """Тест: недостаточно данных для проверки"""
        reservation = Mock()
        reservation.table = None
        reservation.date = None
        reservation.start_time = None
        reservation.status = 'confirmed'

        try:
            result = ReservationValidator.validate_availability(reservation)
            self.assertTrue(result)
        except ValidationError:
            self.fail("Валидатор вызвал исключение при недостатке данных")


class ConcurrentReservationTest(TestCase):
    """Тесты конкурентного бронирования"""

    def setUp(self):
        self.hall = Hall.objects.create(name="Test Hall")
        self.table = Table.objects.create(
            hall=self.hall,
            number="A1",
            capacity=4,
            x_position=1,
            y_position=1,
            is_active=True
        )
        self.user1 = User.objects.create(email='user1@example.com')
        self.user1.set_password('pass123')
        self.user1.save()

        self.user2 = User.objects.create(email='user2@example.com')
        self.user2.set_password('pass123')
        self.user2.save()
        self.client = Client(enforce_csrf_checks=False)

    def test_debug_form_validation(self):
        """Тест для debug: проверяем валидность формы"""
        reservation_date = date.today() + timedelta(days=1)

        form_data = {
            'hall': self.hall.id,
            'table': self.table.id,
            'date': reservation_date.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'guests_count': 2,
            'duration': '03:00:00'
        }
        from reservation.forms import ReservationForm

        form = ReservationForm(data=form_data, user=self.user1)
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")

        self.client.login(email='user1@example.com', password='pass123')
        response = self.client.post(reverse('reservation:reservations_create'), form_data)

        print(f"Response status: {response.status_code}")
        print(f"Response URL: {getattr(response, 'url', 'No redirect')}")
        if response.status_code == 200:
            print(f"Response content (first 200 chars): {response.content.decode()[:200]}")

        print(f"Reservations count: {Reservation.objects.count()}")
        if Reservation.objects.count() > 0:
            reservation = Reservation.objects.first()
            print(f"First reservation: {reservation}")
            print(f"Reservation user: {reservation.user}")
            print(f"Reservation status: {reservation.status}")

    def test_concurrent_reservation_same_time(self):
        """Тест: два пользователя пытаются забронировать один столик"""
        reservation_date = date.today() + timedelta(days=1)

        form_data = {
            'hall': self.hall.id,
            'table': self.table.id,
            'date': reservation_date.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'guests_count': 2,
            'duration': '03:00:00'
        }
        self.client.login(email='user1@example.com', password='pass123')
        response1 = self.client.post(reverse('reservation:reservations_create'), form_data)

        print(f"User1 response: {response1.status_code}")
        if response1.status_code == 200:
            print(
                f"User1 form errors: {response1.context['form'].errors if 'form' in response1.context else 'No form in context'}")
        reservations = Reservation.objects.all()
        print(f"Reservations after user1: {list(reservations)}")

        self.assertEqual(reservations.count(), 1)
        reservation1 = reservations.first()
        self.assertEqual(reservation1.user, self.user1)
        self.client.login(email='user2@example.com', password='pass123')
        self.client.post(reverse('reservation:reservations_create'), form_data)

        print(f"Total reservations: {Reservation.objects.count()}")
        self.assertEqual(Reservation.objects.count(), 1)

    def test_concurrent_reservation_different_times(self):
        """Тест: два пользователя бронируют разное время - должно работать"""
        reservation_date = date.today() + timedelta(days=1)
        form_data1 = {
            'hall': self.hall.id,
            'table': self.table.id,
            'date': reservation_date.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'guests_count': 2,
            'duration': '03:00:00'
        }

        self.client.login(email='user1@example.com', password='pass123')
        self.client.post(reverse('reservation:reservations_create'), form_data1)

        form_data2 = {
            'hall': self.hall.id,
            'table': self.table.id,
            'date': reservation_date.strftime('%Y-%m-%d'),
            'start_time': '17:00',
            'guests_count': 2,
            'duration': '03:00:00'
        }

        self.client.login(email='user2@example.com', password='pass123')
        self.client.post(reverse('reservation:reservations_create'), form_data2)

        print(f"Total reservations: {Reservation.objects.count()}")
        self.assertEqual(Reservation.objects.count(), 2)
        self.assertEqual(Reservation.objects.filter(user=self.user1).count(), 1)
        self.assertEqual(Reservation.objects.filter(user=self.user2).count(), 1)

    def test_simple_reservation_creation(self):
        """Простой тест создания брони без конкурентности"""
        reservation_date = date.today() + timedelta(days=1)

        form_data = {
            'hall': self.hall.id,
            'table': self.table.id,
            'date': reservation_date.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'guests_count': 2,
            'duration': '03:00:00'
        }

        self.client.login(email='user1@example.com', password='pass123')
        response = self.client.post(reverse('reservation:reservations_create'), form_data)

        print(f"Simple test - Status: {response.status_code}")
        print(f"Simple test - Redirect: {getattr(response, 'url', None)}")
        print(f"Simple test - Reservations: {Reservation.objects.count()}")
        if response.status_code == 302:
            follow_response = self.client.get(response.url)
            print(f"Follow response content: {follow_response.content.decode()[:200]}")


class AdminDurationChangeTestCase(TestCase):
    """Тесты для изменения длительности бронирования администратором"""

    def setUp(self):
        self.admin_user = User.objects.create(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )
        self.admin_user.set_password('testpass123')
        self.admin_user.save()

        self.regular_user = User.objects.create(
            email='regular@test.com',
            password='testpass123'
        )
        self.regular_user.set_password('testpass123')
        self.regular_user.save()

        self.hall = Hall.objects.create(
            name='Test Hall',
            width=10,
            height=8
        )

        self.table = Table.objects.create(
            hall=self.hall,
            number='A1',
            capacity=4,
            x_position=1,
            y_position=1,
            is_active=True
        )

        self.reservation = Reservation.objects.create(
            user=self.regular_user,
            table=self.table,
            date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            duration=timedelta(hours=2),
            guests_count=2,
            status='confirmed'
        )

    def test_admin_can_change_duration(self):
        """Тест: администратор может изменить длительность бронирования"""
        self.client.login(email='admin@test.com', password='testpass123')

        new_duration = timedelta(hours=4)
        form_data = {
            'hall': self.hall.id,
            'table': self.table.id,
            'date': self.reservation.date,
            'start_time': self.reservation.start_time,
            'duration': new_duration,
            'guests_count': self.reservation.guests_count,
            'event': ''
        }

        form = ReservationForm(
            data=form_data,
            instance=self.reservation,
            user=self.admin_user
        )
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        self.client.post(
            f'/reservation/update/{self.reservation.id}/',
            form_data
        )
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.duration, new_duration)
        self.assertTrue(self.reservation.extended_by_admin)

    def test_duration_field_editable_for_admins(self):
        """Тест: поле длительности редактируемое у администраторов"""
        self.client.login(email='admin@test.com', password='testpass123')
        response = self.client.get(f'/reservation/update/{self.reservation.id}/')
        self.assertNotContains(response, 'readonly')

    def test_end_time_calculation_after_duration_change(self):
        """Тест: корректный расчет времени окончания после изменения длительности"""
        new_duration = timedelta(hours=5)
        expected_end_time = (
            timezone.datetime.combine(self.reservation.date, self.reservation.start_time) +
            new_duration
        ).time()

        form_data = {
            'hall': self.hall.id,
            'table': self.table.id,
            'date': self.reservation.date,
            'start_time': self.reservation.start_time,
            'duration': new_duration,
            'guests_count': self.reservation.guests_count,
            'event': ''
        }

        form = ReservationForm(
            data=form_data,
            instance=self.reservation,
            user=self.admin_user
        )
        self.assertTrue(form.is_valid())
        reservation = form.save(commit=False)
        self.assertEqual(reservation.end_time, expected_end_time)

    def test_duration_change_with_conflicting_reservation(self):
        """Тест: нельзя изменить длительность, если возникает конфликт"""

        Reservation.objects.create(
            user=self.regular_user,
            table=self.table,
            date=self.reservation.date,
            start_time=time(16, 0),
            duration=timedelta(hours=2),
            guests_count=2,
            status='confirmed'
        )
        self.client.login(email='admin@test.com', password='testpass123')
        new_duration = timedelta(hours=5)
        form_data = {
            'hall': self.hall.id,
            'table': self.table.id,
            'date': self.reservation.date,
            'start_time': self.reservation.start_time,
            'duration': new_duration,
            'guests_count': self.reservation.guests_count,
            'event': ''
        }

        form = ReservationForm(
            data=form_data,
            instance=self.reservation,
            user=self.admin_user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_extended_by_admin_flag_set_correctly(self):
        """Тест: флаг extended_by_admin устанавливается корректно"""
        self.client.login(email='admin@test.com', password='testpass123')
        new_duration = timedelta(hours=4)
        form_data = {
            'hall': self.hall.id,
            'table': self.table.id,
            'date': self.reservation.date,
            'start_time': self.reservation.start_time,
            'duration': new_duration,
            'guests_count': self.reservation.guests_count,
            'event': ''
        }

        self.client.post(
            f'/reservation/update/{self.reservation.id}/',
            form_data
        )
        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.extended_by_admin)
        original_duration = timedelta(hours=2)
        form_data['duration'] = original_duration

        self.client.post(
            f'/reservation/update/{self.reservation.id}/',
            form_data
        )
        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.extended_by_admin)


class CeleryTasksTestCase(TestCase):
    """Тесты для Celery задач"""

    def setUp(self):
        self.user = User.objects.create(
            email='test@example.com',
            first_name='Иван',
            last_name='Петров'
        )
        self.hall = Hall.objects.create(name='Test Hall')
        self.table = Table.objects.create(
            hall=self.hall,
            number='A1',
            capacity=4,
            x_position=1,
            y_position=1,
            is_active=True
        )
        self.reservation = Reservation.objects.create(
            user=self.user,
            table=self.table,
            date=date.today(),
            start_time=time(14, 0),
            duration=timedelta(hours=2),
            guests_count=2,
            status='pending'
        )

    @override_settings(
        SITE_URL='http://testserver',
        DEFAULT_FROM_EMAIL='noreply@restaurant.com',
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True
    )
    def test_send_reservation_reminders_integration(self):
        """Интеграционный тест: Celery task отправляет email"""

        send_reservation_reminders.delay()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn('Подтвердите вашу бронь на сегодня', mail.outbox[0].subject)

    @patch('reservation.tasks.send_confirmation_email')
    def test_send_reservation_reminders_with_mock(self, mock_send_email):
        """Тест: Celery task с mock отправки email"""

        send_reservation_reminders.delay()
        mock_send_email.assert_called_once()
        called_reservation = mock_send_email.call_args[0][0]
        self.assertEqual(called_reservation.id, self.reservation.id)

    def test_send_reservation_reminders_no_reservations(self):
        """Тест: Celery task когда нет броней для напоминаний"""

        self.reservation.delete()
        send_reservation_reminders.delay()

    @patch('reservation.tasks.send_confirmation_email')
    def test_send_reservation_reminders_multiple_reservations(self, mock_send_email):
        """Тест: Celery task с несколькими бронями"""

        user2 = User.objects.create(email='test2@example.com')
        Reservation.objects.create(
            user=user2,
            table=self.table,
            date=date.today(),
            start_time=time(16, 0),
            duration=timedelta(hours=2),
            guests_count=3,
            status='pending'
        )
        send_reservation_reminders.delay()
        self.assertEqual(mock_send_email.call_count, 2)

    @patch('reservation.tasks.send_confirmation_email')
    def test_send_reservation_reminders_only_pending(self, mock_send_email):
        """Тест: Celery task отправляет только pending брони"""

        self.reservation.status = 'confirmed'
        self.reservation.save()
        send_reservation_reminders.delay()
        mock_send_email.assert_not_called()

    @patch('reservation.tasks.send_confirmation_email')
    def test_send_reservation_reminders_only_today(self, mock_send_email):
        """Тест: Celery task отправляет только сегодняшние брони"""

        self.reservation.date = date.today() + timedelta(days=1)
        self.reservation.save()
        send_reservation_reminders.delay()
        mock_send_email.assert_not_called()

    @patch('reservation.tasks.send_confirmation_email')
    def test_send_reservation_reminders_exception_handling(self, mock_send_email):
        """Тест: обработка исключений в Celery task"""

        mock_send_email.side_effect = Exception('Email error')
        with self.assertRaises(Exception) as context:
            send_reservation_reminders()
        self.assertIn('Email error', str(context.exception))


class FillRestaurantDataCommandTest(TestCase):
    """Тесты для кастомной команды наполнения данных ресторана"""

    def test_command_output(self):
        """Тест вывода команды"""
        out = StringIO()
        call_command('fill_restaurant_data', stdout=out)
        output = out.getvalue()
        self.assertEqual(output, '')

    def test_halls_created(self):
        """Тест создания залов"""
        self.assertEqual(Hall.objects.count(), 0)

        call_command('fill_restaurant_data')

        self.assertGreater(Hall.objects.count(), 0)
        self.assertTrue(Hall.objects.filter(name__icontains='зал').exists())

    def test_tables_created(self):
        """Тест создания столиков"""
        self.assertEqual(Table.objects.count(), 0)

        call_command('fill_restaurant_data')

        self.assertGreater(Table.objects.count(), 0)
        tables_with_halls = Table.objects.filter(hall__isnull=False)
        self.assertGreater(tables_with_halls.count(), 0)

    def test_command_idempotent(self):
        """Тест что команду можно запускать多次"""
        call_command('fill_restaurant_data')
        first_count = Hall.objects.count()

        call_command('fill_restaurant_data')
        self.assertEqual(Hall.objects.count(), first_count)

    def test_fixture_file_exists(self):
        """Тест что файл фикстур существует"""
        fixture_path = 'reservation/fixtures/restaurant_data.json'
        self.assertTrue(os.path.exists(fixture_path),
                        f"Fixture file {fixture_path} does not exist")
