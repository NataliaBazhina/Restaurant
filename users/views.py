from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404
from django.urls import reverse
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, DetailView
from users.forms import UserRegisterForm, UserChangePasswordForm, UserUpdateForm
from users.models import User
from django.core.exceptions import ObjectDoesNotExist
from config.settings import EMAIL_HOST_USER
import secrets
from django.db.models import Count, Q


class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
         user = form.save()
         user.is_active = False
         token = secrets.token_hex(16)
         user.token = token
         user.save()
         host = self.request.get_host()
         url = f'http://{host}/users/email-confirm/{token}/'
         send_mail(
             subject='Подтверждение почты',
             message=f'Здравствуйте! Для завершения регистрации пожалуйста перейдите по ссылке {url}.',
             from_email=EMAIL_HOST_USER,
             recipient_list=[user.email]
         )
         return super().form_valid(form)

class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"
    context_object_name = "user_obj"

    def test_func(self):
        """Только админы могут смотреть чужие профили"""
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context["reservations_count"] = user.guest_reservations.count()
        return context


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "users/users_list.html"
    paginate_by = 10
    context_object_name = 'users'

    def test_func(self):
        """Только админы могут видеть список пользователей"""
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_queryset(self):
        """Фильтрация и поиск пользователей"""
        queryset = super().get_queryset()

        # Поиск по email, имени, фамилии
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(phone__icontains=search_query)
            )

        # Сортировка по дате регистрации
        queryset = queryset.order_by('-date_joined')

        return queryset

    def get_context_data(self, **kwargs):
        """Добавляем поисковый запрос в контекст"""
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'users/user_update.html'
    success_url = reverse_lazy('reservation:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлен!')
        return super().form_valid(form)

class UserDeleteView(DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('reservation:home')

    def get_object(self, queryset=None):
        return self.request.user

def email_verification(request, token):
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.save()
    return redirect(reverse('users:login'))

def change_password(
    request,
):
    if request.method == "POST":
        form = UserChangePasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(
                    email=form.cleaned_data.get("email"), is_active=True
                )
            except ObjectDoesNotExist:
                return render(
                    request,
                    "users/change_password.html",
                    {"form": UserChangePasswordForm()},
                )
            else:
                new_password = User.objects.make_random_password(12)
                user.set_password(new_password)
                user.save()
                send_mail(
                    subject="Новый пароль",
                    message=f"Ваш новый пароль: {new_password}",
                    from_email=EMAIL_HOST_USER,
                    recipient_list=[user.email],
                )
                return redirect(reverse("users:login"))
    elif request.method == "GET":
        return render(
            request, "users/change_password.html", {"form": UserChangePasswordForm()}
        )

