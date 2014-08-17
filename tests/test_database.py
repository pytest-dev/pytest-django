from __future__ import with_statement

import pytest
from django.db import connection, transaction
from django.test.testcases import connections_support_transactions

from pytest_django_test.app.models import Item


def noop_transactions():
    """Test whether transactions are disabled.

    Return True if transactions are disabled, False if they are
    enabled.
    """

    # Newer versions of Django simply run standard tests in an atomic block.
    if hasattr(connection, 'in_atomic_block'):
        return connection.in_atomic_block
    else:
        with transaction.commit_manually():
            Item.objects.create(name='transaction_noop_test')
            transaction.rollback()

        try:
            item = Item.objects.get(name='transaction_noop_test')
        except Item.DoesNotExist:
            return False
        else:
            item.delete()
            return True


def test_noaccess():
    with pytest.raises(pytest.fail.Exception):
        Item.objects.create(name='spam')
    with pytest.raises(pytest.fail.Exception):
        Item.objects.count()


@pytest.fixture
def noaccess():
    with pytest.raises(pytest.fail.Exception):
        Item.objects.create(name='spam')
    with pytest.raises(pytest.fail.Exception):
        Item.objects.count()


def test_noaccess_fixture(noaccess):
    # Setup will fail if this test needs to fail
    pass


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
        if not connections_support_transactions():
            pytest.skip('transactions required for this test')

        assert noop_transactions()

    def test_transactions_enabled(self, transactional_db):
        if not connections_support_transactions():
            pytest.skip('transactions required for this test')

        assert not noop_transactions()

    @pytest.fixture
    def mydb(self, both_dbs):
        # This fixture must be able to access the database
        Item.objects.create(name='spam')

    def test_mydb(self, mydb):
        if not connections_support_transactions():
            pytest.skip('transactions required for this test')

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


class TestDatabaseFixturesBothOrder:
    @pytest.fixture
    def fixture_with_db(self, db):
        Item.objects.create(name='spam')

    @pytest.fixture
    def fixture_with_transdb(self, transactional_db):
        Item.objects.create(name='spam')

    def test_trans(self, fixture_with_transdb):
        pass

    def test_db(self, fixture_with_db):
        pass

    def test_db_trans(self, fixture_with_db, fixture_with_transdb):
        pass

    def test_trans_db(self, fixture_with_transdb, fixture_with_db):
        pass


class TestDatabaseMarker:

    @pytest.mark.django_db
    def test_access(self):
        Item.objects.create(name='spam')

    @pytest.mark.django_db
    def test_clean_db(self):
        # Relies on the order: test_access created an object
        assert Item.objects.count() == 0

    @pytest.mark.django_db
    def test_transactions_disabled(self):
        if not connections_support_transactions():
            pytest.skip('transactions required for this test')

        assert noop_transactions()

    @pytest.mark.django_db(transaction=False)
    def test_transactions_disabled_explicit(self):
        if not connections_support_transactions():
            pytest.skip('transactions required for this test')

        assert noop_transactions()

    @pytest.mark.django_db(transaction=True)
    def test_transactions_enabled(self):
        if not connections_support_transactions():
            pytest.skip('transactions required for this test')

        assert not noop_transactions()
