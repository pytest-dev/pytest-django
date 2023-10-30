from django.http import HttpResponse
from django.urls import path


urlpatterns = [
    path("overridden_url/", lambda r: HttpResponse("Overridden urlconf works!")),
]
