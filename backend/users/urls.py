from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, \
    PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.shortcuts import render
from django.urls import path, reverse_lazy
from . import views


app_name = "users"

urlpatterns = [
    path('register/', views.RegisterUser.as_view(),
         name='register'),

    path('email-verification-sent/',
         lambda request: render(request, 'users/email/email_verification_sent.html'),
         name='email_verification_sent'),

    path('login/', views.LoginUser.as_view(),
         name='login'),

    path('logout/', LogoutView.as_view(),
         name='logout'),

    path('password-change/', views.UserPasswordChange.as_view(),
         name="password_change"),

    path('password-change/done/', PasswordChangeDoneView.as_view(
        template_name="users/password_change_done.html"),
        name="password_change_done"),

    path('password-reset/', PasswordResetView.as_view(
        template_name="users/password_reset_form.html",
        email_template_name="users/password_reset_email.html",
        success_url=reverse_lazy("users:password_reset_done")),
        name='password_reset'),

    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name="users/password_reset_done.html"),
        name='password_reset_done'),

    path('password-reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name="users/password_reset_confirm.html",
        success_url=reverse_lazy("users:password_reset_complete")),
        name='password_reset_confirm'),

    path('password-reset/complete/', PasswordResetCompleteView.as_view(
        template_name="users/password_reset_complete.html"),
        name='password_reset_complete'),

    path('profile/', views.ProfileUser.as_view(),
         name='profile'),

    path('registrations-list/', views.RegistrationsListView.as_view(),
         name='registrations_list'),

    path('registration-detail/<int:pk>/', views.RegistrationDetailView.as_view(),
         name='registration_detail'),

    path('registration/toggle-status/<int:pk>/', views.ToggleRegistrationStatusView.as_view(),
         name='registration_toggle_status'),

    path('delete-profile/', views.DeleteProfileView.as_view(),
         name='delete_profile'),
]
