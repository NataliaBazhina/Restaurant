from celery import shared_task
from django.utils import timezone
from datetime import date
from .models import Reservation
from .services import send_confirmation_email


@shared_task
def send_reservation_reminders():
    """Каждый день в 8:00 отправляем подтверждения для броней на сегодня"""
    today = date.today()
    reservations = Reservation.objects.filter(
        date=today,
        status='pending'
    )

    for reservation in reservations:
        send_confirmation_email(reservation)