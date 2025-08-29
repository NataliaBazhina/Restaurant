import requests
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_reservation_confirmation_email(reservation):
    """Отправка email подтверждения брони"""
    try:
        from .views import generate_confirmation_token
        token = generate_confirmation_token(reservation)
        confirmation_url = f"{settings.SITE_URL}/confirm-reservation/{reservation.id}/{token}/"

        subject = 'Подтверждение бронирования на сегодня'
        html_message = render_to_string('reservation/email/confirmation_email.html', {
            'reservation': reservation,
            'confirmation_url': confirmation_url
        })
        plain_message = strip_tags(html_message)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [reservation.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Подтверждение отправлено для брони #{reservation.id}")
        return True

    except Exception as e:
        logger.error(f"Ошибка отправки email для брони #{reservation.id}: {e}")
        return False


def send_confirmation_success_email(reservation):
    """Отправка email об успешном подтверждении"""
    try:
        subject = 'Бронь подтверждена!'
        html_message = render_to_string('reservation/email/confirmation_success.html', {
            'reservation': reservation
        })
        plain_message = strip_tags(html_message)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [reservation.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Уведомление о подтверждении отправлено для брони #{reservation.id}")
        return True

    except Exception as e:
        logger.error(f"Ошибка отправки email подтверждения для брони #{reservation.id}: {e}")
        return False