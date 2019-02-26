from django.http import HttpResponse
from django.template import Template
from django.template.context import Context

from .models import Item


def admin_required_view(request):
    assert request.user.is_staff
    return HttpResponse(Template("You are an admin").render(Context()))


def item_count(request):
    return HttpResponse("Item count: %d" % Item.objects.count())
