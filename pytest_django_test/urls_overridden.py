from django.conf.urls import url
from django.http import HttpResponse

from .compat import patterns

urlpatterns = patterns(
    "", url(r"^overridden_url/$", lambda r: HttpResponse("Overridden urlconf works!"))
)
