from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from django.views import View
from django.views.generic import CreateView


class SignUpView(CreateView):
    template_name = 'auth/login.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('dev:dev-index')

    def form_valid(self, form):
        response = super().form_valid(form)

        uname = form.cleaned_data['username']
        password = form.cleaned_data['password1']

        user = authenticate(self.request, username=uname, password=password)
        if user:
            login(self.request, user)

        return response


class LogoutView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect('auth:login')
        return render(request, 'auth/logout.html')

    def post(self, request: HttpRequest) -> HttpResponse:
        logout(request)
        return redirect('auth:login')
