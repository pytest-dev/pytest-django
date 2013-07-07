"""Test for user-visible fixtures

Not quite all fixtures are tested here, the db and transactional_db
fixtures are tested in test_database.
"""

from __future__ import with_statement

import django
import pytest
from django.conf import settings as real_settings
from django.test.client import Client, RequestFactory

from .app.models import Item
from .test_database import noop_transactions
from .compat import force_text, urlopen


django  # Avoid pyflakes complaints


def test_client(client):
    assert isinstance(client, Client)


@pytest.mark.django_db
def test_admin_client(admin_client):
    assert isinstance(admin_client, Client)
    resp = admin_client.get('/admin-required/')
    assert force_text(resp.content) == 'You are an admin'


def test_admin_client_no_db_marker(admin_client):
    assert isinstance(admin_client, Client)
    resp = admin_client.get('/admin-required/')
    assert force_text(resp.content) == 'You are an admin'


def test_rf(rf):
    assert isinstance(rf, RequestFactory)


class TestSettings:
    """Tests for the settings fixture, order matters"""

    def test_modify_existing(self, settings):
        assert settings.SECRET_KEY == 'foobar'
        assert real_settings.SECRET_KEY == 'foobar'
        settings.SECRET_KEY = 'spam'
        assert settings.SECRET_KEY == 'spam'
        assert real_settings.SECRET_KEY == 'spam'

    def test_modify_existing_again(self, settings):
        assert settings.SECRET_KEY == 'foobar'
        assert real_settings.SECRET_KEY == 'foobar'

    def test_new(self, settings):
        assert not hasattr(settings, 'SPAM')
        assert not hasattr(real_settings, 'SPAM')
        settings.SPAM = 'ham'
        assert settings.SPAM == 'ham'
        assert real_settings.SPAM == 'ham'

    def test_new_again(self, settings):
        assert not hasattr(settings, 'SPAM')
        assert not hasattr(real_settings, 'SPAM')

    def test_deleted(self, settings):
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(real_settings, 'SECRET_KEY')
        del settings.SECRET_KEY
        assert not hasattr(settings, 'SECRET_KEY')
        assert not hasattr(real_settings, 'SECRET_KEY')

    def test_deleted_again(self, settings):
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(real_settings, 'SECRET_KEY')


class TestLiveServer:
    pytestmark = [
        pytest.mark.skipif('django.VERSION[:2] < (1, 4)'),
        pytest.mark.urls('tests.urls_liveserver'),
        ]

    def test_url(self, live_server):
        assert live_server.url == force_text(live_server)

    def test_transactions(self, live_server):
        assert not noop_transactions()

    def test_db_changes_visibility(self, live_server):
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 0'
        Item.objects.create(name='foo')
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 1'

    def test_fixture_db(self, db, live_server):
        Item.objects.create(name='foo')
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 1'

    def test_fixture_transactional_db(self, transactional_db, live_server):
        Item.objects.create(name='foo')
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 1'

    @pytest.fixture
    def item(self):
        # This has not requested database access so should fail.
        # Unfortunately the _live_server_helper autouse fixture makes this
        # test work.
        with pytest.raises(pytest.fail.Exception):
            Item.objects.create(name='foo')

    @pytest.mark.xfail
    def test_item(self, item, live_server):
        # test should fail/pass in setup
        pass

    @pytest.fixture
    def item_db(self, db):
        return Item.objects.create(name='foo')

    def test_item_db(self, item_db, live_server):
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 1'

    @pytest.fixture
    def item_transactional_db(self, transactional_db):
        return Item.objects.create(name='foo')

    def test_item_transactional_db(self, item_transactional_db, live_server):
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 1'
