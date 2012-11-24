from django.http import HttpResponse
from django.template import Template
from django.template.context import Context


def admin_required_view(request):
    if request.user.is_staff:
        return HttpResponse(Template('You are an admin').render(Context()))
    return HttpResponse(Template('Access denied').render(Context()))
