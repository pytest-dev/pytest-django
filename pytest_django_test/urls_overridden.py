from django.conf.urls import patterns, url

from django.http import HttpResponse

urlpatterns = patterns(
    '',
    url(r'^overridden_url/$',
        lambda r: HttpResponse('Overridden urlconf works!'))
)
