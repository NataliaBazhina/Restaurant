from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, UpdateView, DeleteView, TemplateView, DetailView, CreateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from .models import Reservation, Table, Hall
from .forms import ReservationForm, FeedbackForm
from django.utils import timezone
from datetime import datetime, timedelta, date
import logging
from django.core.mail import send_mail
from django.conf import settings

from .validators import ReservationValidator

logger = logging.getLogger(__name__)


class TablesByHallView(View):
    def get(self, request, hall_id):
        try:
            date_str = request.GET.get('date')
            time_str = request.GET.get('time')
            guests_count = request.GET.get('guests')

            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
            time_obj = datetime.strptime(time_str, '%H:%M').time() if time_str else None
            guests = int(guests_count) if guests_count else 1

            tables = Table.objects.filter(hall_id=hall_id, capacity__gte=guests)

            available_tables = []

            for table in tables:
                temp_reservation = Reservation(
                    table=table,
                    date=date_obj,
                    start_time=time_obj,
                    guests_count=guests,
                    duration=timedelta(hours=3)
                )

                try:
                    ReservationValidator.validate_availability(temp_reservation)
                    available_tables.append({
                        'id': table.id,
                        'number': table.number,
                        'capacity': table.capacity
                    })
                except ValidationError:
                    pass


            return JsonResponse({'tables': available_tables})

        except ValueError as e:
            return JsonResponse({'error': f'Неверный формат данных: {e}'}, status=400)
        except Exception as e:
            logger.exception("Error in TablesByHallView:")
            return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)

class HallListView(ListView):
    model = Hall
    template_name = 'reservation/hall_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['halls'] = Hall.objects.all()
        return context


class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'reservation/reservation_form.html'
    success_url = reverse_lazy('reservation:profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            reservation = form.save(commit=False)
            reservation.user = self.request.user
            if reservation.date == timezone.now().date():
                reservation.status = 'confirmed'
                message = f"Бронь подтверждена! Столик #{reservation.table.number}"
            else:
                reservation.status = 'pending'
                message = f"Бронь создана! Подтверждение придет в день бронирования. Столик #{reservation.table.number}"

            reservation.save()

            messages.success(self.request, message)
            return redirect(self.success_url)

        except IntegrityError as e:
            form.add_error(None,
                           'Произошла ошибка при сохранении. Возможно, столик на это время уже был забронирован кем-то другим. Пожалуйста, попробуйте еще раз.')
            return self.form_invalid(form)


class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = 'reservation/reservation_detail.html'
    context_object_name = 'reservation'

    def get_object(self, queryset=None):
        reservation = super().get_object(queryset)
        if reservation.user != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("У вас нет доступа к этому бронированию")
        return reservation


class ReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'reservation/reservation_list.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        now = timezone.now().date()
        Reservation.objects.filter(status='confirmed', date__lt=now).update(status='completed')
        if self.request.user.is_staff:
            return Reservation.objects.all().order_by('-date', '-start_time')
        else:
            return Reservation.objects.filter(user=self.request.user).order_by('-date', '-start_time')


class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'reservation/reservation_form.html'
    success_url = reverse_lazy('reservation:reservations_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        reservation = form.save(commit=False)
        original_duration = Reservation.objects.get(pk=self.object.pk).duration
        if self.request.user.is_staff and original_duration != reservation.duration:
            reservation.extended_by_admin = True
            messages.info(self.request, f"Длительность брони изменена. Новое время окончания: {reservation.end_time}")
        reservation.save()
        messages.success(self.request, "Бронь успешно обновлена!")
        return redirect(self.get_success_url())


class ReservationDeleteView(LoginRequiredMixin, DeleteView):
    model = Reservation
    template_name = 'reservation/reservation_confirm_delete.html'
    success_url = reverse_lazy('reservation:reservations_list')

    def delete(self, request, *args, **kwargs):
        """
        Меняет статус брони на 'canceled'
        """
        reservation = self.get_object()
        reservation.status = 'canceled'
        reservation.save()
        messages.success(request, "Бронь успешно отменена!")
        return redirect(self.success_url)


class AboutView(TemplateView):
    template_name = "reservation/about.html"


class ContactView(TemplateView):
    template_name = "reservation/contact.html"


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'reservation/profile.html'

    def get_context_data(self, **kwargs):
        now = timezone.now().date()
        Reservation.objects.filter(status='confirmed', date__lt=now).update(status='completed')
        context = super().get_context_data(**kwargs)
        user_reservations = Reservation.objects.filter(
            user=self.request.user
        ).order_by('-date', '-start_time')
        today = date.today()
        context['active_reservations'] = user_reservations.filter(
            date__gte=today,
            status='confirmed'
        )
        context['past_reservations'] = user_reservations.filter(
            date__lt=today
        )
        context['user'] = self.request.user

        return context

def home(request):
    return render(request, 'reservation/home.html')

def reservation_welcome(request):
    return render(request, 'reservation/reservation_welcome.html')


def hall_schema(request, hall_id):
    hall = get_object_or_404(Hall, id=hall_id)
    tables = Table.objects.filter(hall=hall, is_active=True)

    grid = [[None for _ in range(hall.width)] for _ in range(hall.height)]

    for table in tables:
        if table.x_position < hall.width and table.y_position < hall.height:
            grid[table.y_position][table.x_position] = table

    return render(request, 'reservation/hall_schema.html', {
        'hall': hall,
        'grid': grid,
        'tables': tables
    })


class ConfirmReservationView(View):
    def get(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, id=reservation_id)

        if reservation.date == date.today() and reservation.status == 'pending':
            reservation.status = 'confirmed'
            reservation.save()
            messages.success(request, "Бронь успешно подтверждена!")
        else:
            messages.error(request, "Нельзя подтвердить эту бронь")

        return redirect('reservation:profile')


class FeedbackView(FormView):
    template_name = "reservation/feedback.html"
    form_class = FeedbackForm
    success_url = reverse_lazy("reservation:feedback_thanks")

    def form_valid(self, form):
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        message = form.cleaned_data['message']

        subject = f'Новое сообщение от {name}'
        email_message = f'''
        Имя: {name}
        Email: {email}
        Сообщение: {message}

        Дата: {timezone.now()}
        '''

        send_mail(
            subject,
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        messages.success(self.request, "Спасибо за ваше сообщение!")
        return super().form_valid(form)


class FeedbackThanksView(TemplateView):
    template_name = "reservation/feedback_thanks.html"