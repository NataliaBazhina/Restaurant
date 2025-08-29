from django.contrib.auth.models import AbstractUser
from django.db import models



class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name='почта', help_text='Введите почту')
    phone = models.CharField(max_length=35, verbose_name='телефон', blank=True, null=True, help_text='Введите номер телефона')
    token = models.CharField(max_length=100, verbose_name= 'token', blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def get_reservations_count(self):
        return self.guest_reservations.count()


    def __str__(self):
        return self.email
