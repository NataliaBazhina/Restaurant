from django.contrib.auth.forms import UserCreationForm
from django import forms
from reservation.forms import StyleFormMixin
from users.models import User


class UserRegisterForm(StyleFormMixin, UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='Имя',
        help_text='Введите ваше настоящее имя'
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='Фамилия',
        help_text='Введите вашу фамилию (необязательно)'
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2')

class UserChangePasswordForm(forms.Form):
    need_generate = forms.BooleanField()
    email =forms.EmailField(required=True)



class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone')
        labels = {
            'email': 'Email',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone': 'Телефон'
        }
        help_texts = {
            'email': 'Ваш email адрес',
            'first_name': 'Введите ваше имя',
            'last_name': 'Введите вашу фамилию',
            'phone': 'Для связи по поводу бронирования'
        }