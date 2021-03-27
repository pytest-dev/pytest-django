from django.urls import path
from django.http import HttpResponse

urlpatterns = [
    path("overridden_url/", lambda r: HttpResponse("Overridden urlconf works!"))
]
