from django.http import HttpRequest, HttpResponse
from django.template import Template
from django.template.context import Context

from .models import Item


def admin_required_view(request: HttpRequest) -> HttpResponse:
    assert request.user.is_staff
    return HttpResponse(Template("You are an admin").render(Context()))


def item_count(request: HttpRequest) -> HttpResponse:
    return HttpResponse(f"Item count: {Item.objects.count()}")
