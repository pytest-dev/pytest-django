import pytest

import django.db
from django.conf import settings as real_settings
from django.test.client import Client, RequestFactory

from app.models import Item
from .test_transactions import noop_transactions


def noop_transactions():
    """Test whether transactions are disabled

    Return True if tranactions are disabled, False if they are
    enabled.
    """
    # A rollback will only work if transactions are enabled.
    # Otherwise the created objects will still exist.
    with django.db.transaction.commit_manually():
        Item.objects.create(name='transaction_noop_test')
        django.db.transaction.rollback()
    try:
        Item.objects.get(name='transaction_noop_test')
    except Exception:
        return False
    else:
        return True


class TestDatabaseFixtures:
    """Tests for the db and transactional_db fixtures"""

    @pytest.fixture(params=['db', 'transactional_db'])
    def both_dbs(self, request):
        if request.param == 'transactional_db':
            return request.getfuncargvalue('transactional_db')
        elif request.param == 'db':
            return request.getfuncargvalue('db')

    def test_access(self, both_dbs):
        Item.objects.create(name='spam')

    def test_clean_db(self, both_dbs):
        # Relies on the order: test_access created an object
        assert Item.objects.count() == 0

    def test_transactions_disabled(self, db):
        assert noop_transactions()

    def test_transactions_enabled(self, transactional_db):
        assert not noop_transactions()

    @pytest.fixture
    def mydb(self, both_dbs):
        # This fixture must be able to access the database
        Item.objects.create(name='spam')

    def test_mydb(self, mydb):
        # Check the fixture had access to the db
        item = Item.objects.get(name='spam')
        assert item

    def test_fixture_clean(self, both_dbs):
        # Relies on the order: test_mydb created an object
        # See https://github.com/pelme/pytest_django/issues/17
        assert Item.objects.count() == 0

    @pytest.fixture
    def fin(self, request, both_dbs):
        # This finalizer must be able to access the database
        request.addfinalizer(lambda: Item.objects.create(name='spam'))

    def test_fin(self, fin):
        # Check finalizer has db access (teardown will fail if not)
        pass


def test_client(client):
    assert isinstance(client, Client)


@pytest.mark.django_db
def test_admin_client(admin_client):
    assert isinstance(admin_client, Client)
    assert admin_client.get('/admin-required/').content == 'You are an admin'


def test_admin_client_no_db_marker(admin_client):
    assert isinstance(admin_client, Client)
    assert admin_client.get('/admin-required/').content == 'You are an admin'


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
