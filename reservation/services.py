from django.core.mail import send_mail
from django.conf import settings

def send_confirmation_email(reservation):
    """Отправка email с ссылкой подтверждения"""
    subject = 'Подтвердите вашу бронь на сегодня'
    message = f'''
Подтвердите бронь на сегодня!

Столик: #{reservation.table.number}
Дата: {reservation.date}
Время: {reservation.start_time}
Гостей: {reservation.guests_count}

Для подтверждения перейдите по ссылке:
{settings.SITE_URL}/confirm-reservation/{reservation.id}/

Если не подтвердите, бронь будет автоматически отменена.
'''
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.user.email],
        fail_silently=False,
    )