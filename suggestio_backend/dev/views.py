from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from dev.models import Entity

@cache_page(60)
def demo_view(request: HttpRequest) -> HttpResponse:
    context = {
        'entities': Entity.objects.all()
    }
    return render(request, 'dev/index.html', context=context)
