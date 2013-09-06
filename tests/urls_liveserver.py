from django.conf.urls import patterns, url
from django.http import HttpResponse

from .app.models import Item

urlpatterns = patterns(
    '',
    url(r'^item_count/$',
        lambda r: HttpResponse('Item count: %d' % Item.objects.count()))
)
