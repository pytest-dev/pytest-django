from django.http import HttpResponse
from django.template import Template

def admin_required_view(request):
    if request.user.is_staff:
        return HttpResponse(Template('You are an admin').render({}))
    return HttpResponse(Template('Access denied').render({}))
