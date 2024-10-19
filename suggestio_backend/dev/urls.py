from django.contrib import admin
from django.urls import path
from django.urls import include

import debug_toolbar

from dev.views import demo_view

app_name = 'dev'

urlpatterns = [
    path('', demo_view, name='dev-index'),
]
