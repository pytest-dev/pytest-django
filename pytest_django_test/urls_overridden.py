from django.conf.urls import url
from django.http import HttpResponse

urlpatterns = [
    url(r"^overridden_url/$", lambda r: HttpResponse("Overridden urlconf works!"))
]
