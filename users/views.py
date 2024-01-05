from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView, LogoutView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, UpdateView, ListView, DetailView

from race_project import settings
from .forms import LoginUserForm, RegisterUserForm, ProfileUserForm, UserPasswordChangeForm
from race.models import EventRegistration

from django_email_verification import send_email


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}


# class RegisterUser(CreateView):
#     form_class = RegisterUserForm
#     template_name = 'users/register.html'
#     extra_context = {'title': "Регистрация"}
#     success_url = reverse_lazy('users:login')

class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': "Регистрация"}
    success_url = reverse_lazy('users:email_verification_sent')  # URL-адрес для перенаправления после регистрации

    def form_valid(self, form):
        # Создаем пользователя, но пока не сохраняем в базу данных
        user = form.save(commit=False)
        # Устанавливаем пользователя как неактивного
        user.is_active = False
        # Сохраняем пользователя
        user.save()
        # Отправляем email для верификации
        send_email(user)
        # Вызываем родительский метод form_valid
        return super().form_valid(form)


class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'
    extra_context = {
        'title': "Профиль пользователя",
        'default_image': settings.DEFAULT_USER_IMAGE,
    }

    def get_success_url(self):
        return reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        # Возвращаем текущего пользователя для обновления
        return self.request.user


class UserPasswordChange(LoginRequiredMixin, PasswordChangeView):
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("users:password_change_done")
    template_name = "users/password_change_form.html"


class RegistrationsListView(LoginRequiredMixin, ListView):
    """A view for listing a user's event registrations."""
    model = EventRegistration
    template_name = 'users/registrations_list.html'
    context_object_name = 'registrations'
    paginate_by = 5

    def get_queryset(self):
        # Получение регистраций
        return self.request.user.registrations.order_by('-registered_at')


class RegistrationDetailView(LoginRequiredMixin, DetailView):
    """A view for displaying the details of an individual event registration."""
    model = EventRegistration
    template_name = 'users/registration_detail.html'
    context_object_name = 'registration'

    def get_queryset(self):
        # Убедитесь, что пользователи могут видеть только свои регистрации
        return EventRegistration.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()  # Добавление текущего времени в контекст
        return context


class ToggleRegistrationStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        registration = get_object_or_404(EventRegistration, pk=pk, user=request.user, event__start_datetime__gte=timezone.now())

        if registration:
            registration.is_active = not registration.is_active
            registration.save()
            message = "Регистрация успешно отменена." if not registration.is_active else "Регистрация восстановлена."
            messages.success(request, message)
        else:
            messages.error(request, "Не удалось изменить статус регистрации.")

        return HttpResponseRedirect(reverse_lazy('users:registration_detail', kwargs={'pk': pk}))
