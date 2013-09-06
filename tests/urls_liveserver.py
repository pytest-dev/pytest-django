try:
    from django.conf.urls import patterns, url  # Django >1.4
except ImportError:
    from django.conf.urls.defaults import patterns, url  # Django 1.3


from django.http import HttpResponse

from .app.models import Item

urlpatterns = patterns(
    '',
    url(r'^item_count/$',
        lambda r: HttpResponse('Item count: %d' % Item.objects.count()))
)
