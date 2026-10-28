from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import LoginForm, SignupForm


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm


class AccountLogoutView(LogoutView):
    pass


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("accounts:login")
