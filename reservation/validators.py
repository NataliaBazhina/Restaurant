from datetime import timezone
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import time, timedelta
from datetime import timedelta





#
#
# class TableValidator:
#     @staticmethod
#     def validate_table_position(table):
#         """Проверка позиции столика в пределах зала"""
#         if table.x_position >= table.hall.width:
#             raise ValidationError(
#                 f"Позиция X ({table.x_position}) превышает ширину зала ({table.hall.width})"
#             )
#         if table.y_position >= table.hall.height:
#             raise ValidationError(
#                 f"Позиция Y ({table.y_position}) превышает длину зала ({table.hall.height})"
#             )
#
#     @staticmethod
#     def validate_table_number_uniqueness(table):
#         """Проверка уникальности номера столика в зале"""
#         from .models import Table
#         if (
#                 Table.objects.filter(hall=table.hall, number=table.number)
#                         .exclude(pk=table.pk)
#                         .exists()
#         ):
#             raise ValidationError(
#                 f"Столик с номером {table.number} уже существует в этом зале"
#             )
#
#
class ReservationValidator:
    @staticmethod
    def validate_guests_count(reservation):
        """Проверка количества гостей"""
        if reservation.guests_count is None:
            raise ValidationError(
                "Количество гостей обязательно для заполнения",
                code='guests_count'
            )
        if reservation.guests_count < 1:
            raise ValidationError(
                "Количество гостей должно быть не менее 1.",
                code='guests_count'
            )
        if reservation.table and reservation.guests_count > reservation.table.capacity:
            raise ValidationError(
                f"Количество гостей ({reservation.guests_count}) "
                f"превышает вместимость столика ({reservation.table.capacity}).",
                code='guests_count'
            )

    @staticmethod
    def validate_date_not_in_past(date_val):
        """Проверка что дата не в прошлом"""
        if date_val is None:
            raise ValidationError(
                "Дата обязательна для заполнения",
                code='date'
            )
        if date_val < timezone.now().date():
            raise ValidationError(
                "Нельзя забронировать столик на прошедшую дату",
                code='date'
            )

    @staticmethod
    def validate_working_hours(time_val):
        """Проверка времени работы ресторана"""
        if time_val is None:
            raise ValidationError(
                "Время начала обязательно для заполнения",
                code='start_time'
            )
        if time_val < time(10, 0) or time_val > time(22, 0):
            raise ValidationError(
                "Ресторан работает с 10:00 до 23:00. Пожалуйста выберите другое время.",
                code='start_time'
            )

    @staticmethod
    def validate_availability(reservation):
        """Проверка доступности столика"""
        from .models import Reservation
        from datetime import datetime

        if not all([reservation.table, reservation.date, reservation.start_time]):
            return True

        if reservation.status == "canceled":
            return True

        new_start = datetime.combine(reservation.date, reservation.start_time)
        new_end = new_start + reservation.duration

        existing_reservations = Reservation.objects.filter(
            table=reservation.table,
            date=reservation.date,
            status__in=["confirmed", "completed"],
        ).exclude(pk=reservation.pk if reservation.pk else None)

        for existing in existing_reservations:
            existing_start = datetime.combine(existing.date, existing.start_time)
            existing_end = existing_start + existing.duration

            if new_start < existing_end and new_end > existing_start:
                raise ValidationError(
                    f"Столик уже забронирован с {existing.start_time} "
                    f"до {existing_end.time()}",
                    code='table'
                )

        return True


class FormValidator:
    @staticmethod
    def validate_reservation_form(data, instance=None):
        """
        Валидация данных формы бронирования.
        """
        from datetime import timedelta
        from .models import Reservation

        table = data.get('table')
        guests_count = data.get('guests_count')
        date_val = data.get('date')
        start_time_val = data.get('start_time')

        if not all([table, date_val, start_time_val, guests_count]):
            raise ValidationError(
                "Все обязательные поля должны быть заполнены",
                code='__all__'
            )

        reservation = Reservation(
            table=table,
            guests_count=guests_count,
            date=date_val,
            start_time=start_time_val,
            duration=timedelta(hours=3),
            pk=instance.pk if instance else None
        )

        try:
            ReservationValidator.validate_date_not_in_past(date_val)
            ReservationValidator.validate_working_hours(start_time_val)
            ReservationValidator.validate_guests_count(reservation)
            ReservationValidator.validate_availability(reservation)
        except ValidationError as e:
            field_name = e.code if e.code != '__all__' else None
            raise ValidationError(e.message, code=field_name)

        return True