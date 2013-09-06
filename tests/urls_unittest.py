from django.conf.urls import patterns, url
from django.http import HttpResponse

urlpatterns = patterns(
    '',
    url(r'^test_url/$', lambda r: HttpResponse('Test URL works!'))
)
