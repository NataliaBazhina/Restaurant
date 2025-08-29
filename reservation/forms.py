from django import forms
from django.core.exceptions import ValidationError
from django.forms import BooleanField
from reservation.models import Reservation, Hall
from reservation.validators import FormValidator


class StyleFormMixin:
    """
    Миксин для добавления CSS-классов ко всем полям формы.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, BooleanField):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class ReservationForm(StyleFormMixin, forms.ModelForm):
    """
    Форма для создания и редактирования бронирования столика.
    Только для авторизованных пользователей.
    """

    hall = forms.ModelChoiceField(
        queryset=Hall.objects.all(),
        label="Выберите зал",
        required=True,
        empty_label="-- Выберите зал --",
        help_text="Выберите зал, в котором хотите забронировать столик"
    )

    class Meta:
        model = Reservation
        fields = ["guests_count", "date", "start_time", "hall", "table", "event", "duration"]
        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'format': 'dd.mm.yyyy',
                    'class': 'form-control'
                }
            ),
            'start_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control'
                }
            ),
            'duration': forms.TextInput(attrs={
                'placeholder': 'ЧЧ:ММ:СС',
                'pattern': '[0-9]{1,2}:[0-5][0-9]:[0-5][0-9]'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.table:
            self.fields['hall'].initial = self.instance.table.hall
        if not (self.user and self.user.is_staff):
            self.fields['duration'].widget.attrs['readonly'] = True
            self.fields['duration'].help_text = "Только для администраторов"

    def clean(self):
        """
        Общая валидация формы через FormValidator.
        """
        cleaned_data = super().clean()

        try:
            FormValidator.validate_reservation_form(cleaned_data, self.instance)
        except ValidationError as e:
            field_name = e.code if hasattr(e, 'code') else None
            if field_name and field_name != '__all__':
                self.add_error(field_name, e)
            else:
                self.add_error(None, e)

        return cleaned_data

class FeedbackForm(forms.Form):
    name = forms.CharField(max_length=100, label="Ваше имя")
    email = forms.EmailField(label="Email")
    message = forms.CharField(widget=forms.Textarea, label="Сообщение")