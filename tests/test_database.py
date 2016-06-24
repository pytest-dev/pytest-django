from __future__ import with_statement

import pytest
from django.db import connection, transaction
from django.test.testcases import connections_support_transactions

from pytest_django.lazy_django import get_django_version
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


@pytest.mark.skipif(
    get_django_version() < (1, 8),
    reason="shared_db_wrapper needs at least Django 1.8")
def test_shared_db_wrapper(django_testdir):
    django_testdir.create_test_module('''
        from .app.models import Item
        import pytest
        from uuid import uuid4

        @pytest.fixture(scope='session')
        def session_item(request, shared_db_wrapper):
            with shared_db_wrapper(request):
                return Item.objects.create(name='session-' + uuid4().hex)

        @pytest.fixture(scope='module')
        def module_item(request, shared_db_wrapper):
            with shared_db_wrapper(request):
                return Item.objects.create(name='module-' + uuid4().hex)

        @pytest.fixture(scope='class')
        def class_item(request, shared_db_wrapper):
            with shared_db_wrapper(request):
                return Item.objects.create(name='class-' + uuid4().hex)

        @pytest.fixture
        def function_item(db):
            return Item.objects.create(name='function-' + uuid4().hex)

        class TestItems:
            def test_save_the_items(
                    self, session_item, module_item, class_item,
                    function_item, db):
                global _session_item
                global _module_item
                global _class_item
                assert session_item.pk
                assert module_item.pk
                assert class_item.pk
                _session_item = session_item
                _module_item = module_item
                _class_item = class_item

            def test_mixing_with_non_db_tests(self):
                pass

            def test_accessing_the_same_items(
                    self, db, session_item, module_item, class_item):
                assert _session_item.name == session_item.name
                Item.objects.get(pk=_session_item.pk)
                assert _module_item.name == module_item.name
                Item.objects.get(pk=_module_item.pk)
                assert _class_item.name == class_item.name
                Item.objects.get(pk=_class_item.pk)

        def test_mixing_with_other_db_tests(db):
            Item.objects.get(name=_module_item.name)
            assert Item.objects.filter(name__startswith='function').count() == 0

        class TestSharing:
            def test_sharing_some_items(
                    self, db, session_item, module_item, class_item,
                    function_item):
                assert _session_item.name == session_item.name
                assert _module_item.name == module_item.name
                assert _class_item.name != class_item.name
                assert Item.objects.filter(name__startswith='function').count() == 1
    ''')
    result = django_testdir.runpytest_subprocess('-v', '-s', '--reuse-db')
    assert result.ret == 0


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
        # See https://github.com/pytest-dev/pytest-django/issues/17
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
    "Tests for the django_db marker."

    @pytest.mark.django_db
    def test_access(self):
        Item.objects.create(name='spam')

    @pytest.mark.django_db
    def test_clean_db(self):
        # Relies on the order: test_access created an object.
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


def test_unittest_interaction(django_testdir):
    "Test that (non-Django) unittests cannot access the DB."

    django_testdir.create_test_module('''
        import pytest
        import unittest
        from .app.models import Item

        class TestCase_setupClass(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                Item.objects.create(name='foo')

            def test_db_access_1(self):
                Item.objects.count() == 1

        class TestCase_setUp(unittest.TestCase):
            @classmethod
            def setUp(cls):
                Item.objects.create(name='foo')

            def test_db_access_2(self):
                Item.objects.count() == 1

        class TestCase(unittest.TestCase):
            def test_db_access_3(self):
                Item.objects.count() == 1
    ''')

    result = django_testdir.runpytest_subprocess('-v', '--reuse-db')
    result.stdout.fnmatch_lines([
        "*test_db_access_1 ERROR*",
        "*test_db_access_2 FAILED*",
        "*test_db_access_3 FAILED*",
        "*ERROR at setup of TestCase_setupClass.test_db_access_1*",
        "*Failed: Database access not allowed, use the \"django_db\" mark to enable*",
    ])
