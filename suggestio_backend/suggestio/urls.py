from django.contrib import admin
from django.urls import path
from django.urls import include

from suggestio.views import AccessView, CallbackView, TestRequestView

app_name = 'suggestio'

urlpatterns = [
    path('access', AccessView.as_view(), name='spotify-access'),
    path('callback/', CallbackView.as_view(), name='spotify-callback'),
    path('test/', TestRequestView.as_view(), name='spotify-test-request'),
]
