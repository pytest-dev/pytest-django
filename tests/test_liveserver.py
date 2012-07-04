import urllib
import django
import pytest

from .app.models import Item
from .test_transactions import django_transactions_is_noops

is_not_django_14_or_newer = repr(django.VERSION[:2] < (1, 4))


def _test_live_server(live_server):

    # Make sure we are running with real transactions
    assert not django_transactions_is_noops()

    Item.objects.create(name='foo')

    response_data = urllib.urlopen(live_server + '/item_count/').read()
    assert response_data == 'Item count: 1'

    Item.objects.create(name='bar')

    response_data = urllib.urlopen(live_server + '/item_count/').read()
    assert response_data == 'Item count: 2'


@pytest.mark.urls('tests.urls_liveserver')
@pytest.mark.skipif(is_not_django_14_or_newer)
def test_live_server_funcarg(live_server):
    _test_live_server(live_server)


@pytest.mark.urls('tests.urls_liveserver')
@pytest.mark.skipif(is_not_django_14_or_newer)
def test_live_server_url_funcarg_again(live_server):
    _test_live_server(live_server)


def pytest_funcarg__created_item(request):
    return Item.objects.create(name='created by a funcarg')


@pytest.mark.skipif(is_not_django_14_or_newer)
@pytest.mark.urls('tests.urls_liveserver')
def test_live_server_created_item(created_item, live_server):
    # Make sure created_item exists from the live_server
    response_data = urllib.urlopen(live_server + '/item_count/').read()
    assert response_data == 'Item count: 1'
