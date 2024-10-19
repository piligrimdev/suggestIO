from django.contrib.auth.views import LoginView
from django.urls import path
from auth.views import SignUpView, LogoutView

app_name = 'auth'

urlpatterns = [
    # вместо собсвтенных View можно использовать собсвтенный с настройками:
    # для выбора пути для перенаправления надо указать url в файле settings.py проекта
    path('login/', LoginView.as_view(template_name="auth/login.html",
                                    redirect_authenticated_user=True), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup')
]
