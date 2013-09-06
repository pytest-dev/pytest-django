try:
    from django.conf.urls import patterns, url  # Django >1.4
except ImportError:
    from django.conf.urls.defaults import patterns, url  # Django 1.3

from django.http import HttpResponse

urlpatterns = patterns(
    '',
    url(r'^overridden_url/$',
        lambda r: HttpResponse('Overridden urlconf works!'))
)
