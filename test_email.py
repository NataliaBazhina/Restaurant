import os
import django
import sys

# Добавляем текущую директорию в Python path
sys.path.append('/app')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("Testing email configuration...")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

try:
    result = send_mail(
        'Test Subject from Docker',
        'This is a test email from Docker container',
        'nataliaagapova27@yandex.ru',
        ['nataliaagapova27@yandex.ru'],
        fail_silently=False,
    )
    print(f"✅ Email sent successfully! Result: {result}")
except Exception as e:
    print(f"❌ Error sending email: {e}")
    import traceback
    traceback.print_exc()