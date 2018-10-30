from __future__ import with_statement

import pytest
from django.db import connection
from django.test.testcases import connections_support_transactions

from pytest_django_test.app.models import Item


def db_supports_reset_sequences():
    """Return if the current db engine supports `reset_sequences`."""
    return (
        connection.features.supports_transactions
        and connection.features.supports_sequence_reset
    )


def test_noaccess():
    with pytest.raises(pytest.fail.Exception):
        Item.objects.create(name="spam")
    with pytest.raises(pytest.fail.Exception):
        Item.objects.count()


@pytest.fixture
def noaccess():
    with pytest.raises(pytest.fail.Exception):
        Item.objects.create(name="spam")
    with pytest.raises(pytest.fail.Exception):
        Item.objects.count()


def test_noaccess_fixture(noaccess):
    # Setup will fail if this test needs to fail
    pass


@pytest.fixture
def non_zero_sequences_counter(db):
    """Ensure that the db's internal sequence counter is > 1.

    This is used to test the `reset_sequences` feature.
    """
    item_1 = Item.objects.create(name="item_1")
    item_2 = Item.objects.create(name="item_2")
    item_1.delete()
    item_2.delete()


class TestDatabaseFixtures:
    """Tests for the different database fixtures."""

    @pytest.fixture(params=["db", "transactional_db", "django_db_reset_sequences"])
    def all_dbs(self, request):
        if request.param == "django_db_reset_sequences":
            return request.getfixturevalue("django_db_reset_sequences")
        elif request.param == "transactional_db":
            return request.getfixturevalue("transactional_db")
        elif request.param == "db":
            return request.getfixturevalue("db")

    def test_access(self, all_dbs):
        Item.objects.create(name="spam")

    def test_clean_db(self, all_dbs):
        # Relies on the order: test_access created an object
        assert Item.objects.count() == 0

    def test_transactions_disabled(self, db):
        if not connections_support_transactions():
            pytest.skip("transactions required for this test")

        assert connection.in_atomic_block

    def test_transactions_enabled(self, transactional_db):
        if not connections_support_transactions():
            pytest.skip("transactions required for this test")

        assert not connection.in_atomic_block

    def test_transactions_enabled_via_reset_seq(self, django_db_reset_sequences):
        if not connections_support_transactions():
            pytest.skip("transactions required for this test")

        assert not connection.in_atomic_block

    def test_django_db_reset_sequences_fixture(
        self, db, django_testdir, non_zero_sequences_counter
    ):

        if not db_supports_reset_sequences():
            pytest.skip(
                "transactions and reset_sequences must be supported "
                "by the database to run this test"
            )

        # The test runs on a database that already contains objects, so its
        # id counter is > 1. We check for the ids of newly created objects.
        django_testdir.create_test_module(
            """
            import pytest
            from .app.models import Item

            def test_django_db_reset_sequences_requested(
                    django_db_reset_sequences):
                item = Item.objects.create(name='new_item')
                assert item.id == 1
        """
        )

        result = django_testdir.runpytest_subprocess("-v", "--reuse-db")
        result.stdout.fnmatch_lines(
            ["*test_django_db_reset_sequences_requested PASSED*"]
        )

    @pytest.fixture
    def mydb(self, all_dbs):
        # This fixture must be able to access the database
        Item.objects.create(name="spam")

    def test_mydb(self, mydb):
        if not connections_support_transactions():
            pytest.skip("transactions required for this test")

        # Check the fixture had access to the db
        item = Item.objects.get(name="spam")
        assert item

    def test_fixture_clean(self, all_dbs):
        # Relies on the order: test_mydb created an object
        # See https://github.com/pytest-dev/pytest-django/issues/17
        assert Item.objects.count() == 0

    @pytest.fixture
    def fin(self, request, all_dbs):
        # This finalizer must be able to access the database
        request.addfinalizer(lambda: Item.objects.create(name="spam"))

    def test_fin(self, fin):
        # Check finalizer has db access (teardown will fail if not)
        pass


class TestDatabaseFixturesAllOrder:
    @pytest.fixture
    def fixture_with_db(self, db):
        Item.objects.create(name="spam")

    @pytest.fixture
    def fixture_with_transdb(self, transactional_db):
        Item.objects.create(name="spam")

    @pytest.fixture
    def fixture_with_reset_sequences(self, django_db_reset_sequences):
        Item.objects.create(name="spam")

    def test_trans(self, fixture_with_transdb):
        pass

    def test_db(self, fixture_with_db):
        pass

    def test_db_trans(self, fixture_with_db, fixture_with_transdb):
        pass

    def test_trans_db(self, fixture_with_transdb, fixture_with_db):
        pass

    def test_reset_sequences(
        self, fixture_with_reset_sequences, fixture_with_transdb, fixture_with_db
    ):
        pass


class TestDatabaseMarker:
    "Tests for the django_db marker."

    @pytest.mark.django_db
    def test_access(self):
        Item.objects.create(name="spam")

    @pytest.mark.django_db
    def test_clean_db(self):
        # Relies on the order: test_access created an object.
        assert Item.objects.count() == 0

    @pytest.mark.django_db
    def test_transactions_disabled(self):
        if not connections_support_transactions():
            pytest.skip("transactions required for this test")

        assert connection.in_atomic_block

    @pytest.mark.django_db(transaction=False)
    def test_transactions_disabled_explicit(self):
        if not connections_support_transactions():
            pytest.skip("transactions required for this test")

        assert connection.in_atomic_block

    @pytest.mark.django_db(transaction=True)
    def test_transactions_enabled(self):
        if not connections_support_transactions():
            pytest.skip("transactions required for this test")

        assert not connection.in_atomic_block

    @pytest.mark.django_db
    def test_reset_sequences_disabled(self, request):
        marker = request.node.get_closest_marker("django_db")
        assert not marker.kwargs

    @pytest.mark.django_db(reset_sequences=True)
    def test_reset_sequences_enabled(self, request):
        marker = request.node.get_closest_marker("django_db")
        assert marker.kwargs["reset_sequences"]


def test_unittest_interaction(django_testdir):
    "Test that (non-Django) unittests cannot access the DB."

    django_testdir.create_test_module(
        """
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
    """
    )

    result = django_testdir.runpytest_subprocess("-v", "--reuse-db")
    result.stdout.fnmatch_lines(
        [
            "*test_db_access_1 ERROR*",
            "*test_db_access_2 FAILED*",
            "*test_db_access_3 FAILED*",
            "*ERROR at setup of TestCase_setupClass.test_db_access_1*",
            '*Failed: Database access not allowed, use the "django_db" mark, '
            'or the "db" or "transactional_db" fixtures to enable it.',
        ]
    )


class Test_database_blocking:
    def test_db_access_in_conftest(self, django_testdir):
        """Make sure database access in conftest module is prohibited."""

        django_testdir.makeconftest(
            """
            from tpkg.app.models import Item
            Item.objects.get()
        """
        )

        result = django_testdir.runpytest_subprocess("-v")
        result.stderr.fnmatch_lines(
            [
                '*Failed: Database access not allowed, use the "django_db" mark, '
                'or the "db" or "transactional_db" fixtures to enable it.*'
            ]
        )

    def test_db_access_in_test_module(self, django_testdir):
        django_testdir.create_test_module(
            """
            from tpkg.app.models import Item
            Item.objects.get()
        """
        )

        result = django_testdir.runpytest_subprocess("-v")
        result.stdout.fnmatch_lines(
            [
                '*Failed: Database access not allowed, use the "django_db" mark, '
                'or the "db" or "transactional_db" fixtures to enable it.'
            ]
        )
