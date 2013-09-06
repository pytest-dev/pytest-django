try:
    from django.conf.urls import patterns, url  # Django >1.4
except ImportError:
    from django.conf.urls.defaults import patterns, url  # Django 1.3

from django.http import HttpResponse

urlpatterns = patterns(
    '',
    url(r'^test_url/$', lambda r: HttpResponse('Test URL works!'))
)
