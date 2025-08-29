from datetime import timedelta
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime

from reservation.validators import ReservationValidator


class Hall(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название зала")
    description = models.TextField(blank=True, verbose_name="Описание зала")
    image = models.ImageField(
        upload_to='halls/',
        blank=True,
        null=True,
        verbose_name="Изображение зала")
    width = models.PositiveSmallIntegerField(
        verbose_name="Ширина зала (столики)",
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        default=10,
    )
    height = models.PositiveSmallIntegerField(
        verbose_name="Длина зала (столики)",
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        default=8,
    )

    class Meta:
        verbose_name = "Зал ресторана"
        verbose_name_plural = "Залы ресторана"

    def __str__(self):
        return self.name

    @property
    def total_capacity(self):
        """Общая вместимость всех столиков в зале"""
        from django.db.models import Sum
        return self.tables.aggregate(
            total=Sum('capacity')
        )['total'] or 0

    @property
    def active_tables_count(self):
        """Количество активных столиков"""
        return self.tables.filter(is_active=True).count()


class Table(models.Model):
    hall = models.ForeignKey(
        Hall, on_delete=models.CASCADE, verbose_name="Зал", related_name="tables"
    )
    number = models.CharField(max_length=10, verbose_name="Номер столика")
    capacity = models.PositiveSmallIntegerField(
        verbose_name="Вместимость",
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    x_position = models.PositiveSmallIntegerField(verbose_name="Позиция X")
    y_position = models.PositiveSmallIntegerField(verbose_name="Позиция Y")
    is_active = models.BooleanField(default=True, verbose_name="Доступен для брони")

    class Meta:
        verbose_name = "Столик"
        verbose_name_plural = "Столики"
        ordering = ["hall", "number"]
        unique_together = ["hall", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["hall", "x_position", "y_position"],
                name="unique_table_position",
            )
        ]

    def __str__(self):
        return f"Столик #{self.number} ({self.hall.name})"

    @classmethod
    def get_tables_by_hall(cls, hall_id):
        """Возвращает столики для зала в формате для JSON"""
        tables = cls.objects.filter(
            hall_id=hall_id,
            is_active=True
        ).values('id', 'number', 'capacity')
        return list(tables)



class Reservation(models.Model):
    STATUS_CHOICES = (
        ("pending", "Ожидает подтверждения"),
        ("confirmed", "Подтверждено"),
        ("canceled", "Отменено"),
        ("completed", "Завершено"),
    )

    SOURCE_CHOICES = (
        ("guest", "Гость через сайт"),
        ("admin", "Администратор вручную"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name='guest_reservations'
    )
    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name="Столик")
    date = models.DateField(verbose_name="Дата бронирования")
    start_time = models.TimeField(verbose_name="Время начала")
    duration = models.DurationField(
        verbose_name="Длительность брони",
        default=timedelta(hours=3),
        help_text="По умолчанию 3 часа. Меняется только админом",
    )
    guests_count = models.PositiveSmallIntegerField(
        verbose_name="Количество гостей"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="confirmed", verbose_name="Статус"
    )
    event = models.TextField(
        blank=True,
        null=True,
        verbose_name="Событие",
        help_text="Планируется ли какое-то событие? Например, день рождения.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    extended_by_admin = models.BooleanField(
        verbose_name="Продлена вручную", default=False
    )
    source = models.CharField(
        verbose_name="Источник брони",
        max_length=20,
        choices=SOURCE_CHOICES,
        default="guest",
        help_text="Кем оформлена бронь",
    )
    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Менеджер/админ",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='staff_reservations',
        help_text="Если бронь оформлялась персоналом",
    )

    class Meta:
        verbose_name = "Бронь"
        verbose_name_plural = "Брони"
        ordering = ["-date", "-start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["table", "date", "start_time"], name="unique_reservation"
            )
        ]

    def __str__(self):
        return f"Бронь #{self.id} - {self.user.username} - {self.date} {self.start_time}"

    @property
    def end_time(self):
        start_datetime = datetime.combine(self.date, self.start_time)
        end_datetime = start_datetime + self.duration
        return end_datetime.time()

    def clean(self):
        """
        Валидация при сохранении через админку.
        """
        ReservationValidator.validate_date_not_in_past(self.date)
        ReservationValidator.validate_working_hours(self.start_time)
        ReservationValidator.validate_guests_count(self)
        ReservationValidator.validate_availability(self)

