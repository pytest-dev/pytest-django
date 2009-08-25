from django.conf.urls.defaults import *
from django.http import HttpResponse

urlpatterns = patterns('',
    url(r'^test_url/$', lambda r: HttpResponse('Test URL works!'))
)
