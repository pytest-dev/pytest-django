from __future__ import annotations

from typing import Generator

import pytest
from django.db import connection, transaction

from .helpers import DjangoPytester

from pytest_django_test.app.models import Item, SecondItem


def db_supports_reset_sequences() -> bool:
    """Return if the current db engine supports `reset_sequences`."""
    ret: bool = (
        connection.features.supports_transactions and connection.features.supports_sequence_reset
    )
    return ret


def test_noaccess() -> None:
    with pytest.raises(RuntimeError):
        Item.objects.create(name="spam")
    with pytest.raises(RuntimeError):
        Item.objects.count()


@pytest.fixture
def noaccess() -> None:
    with pytest.raises(RuntimeError):
        Item.objects.create(name="spam")
    with pytest.raises(RuntimeError):
        Item.objects.count()


def test_noaccess_fixture(noaccess: None) -> None:
    # Setup will fail if this test needs to fail
    pass


@pytest.fixture
def non_zero_sequences_counter(db: None) -> None:
    """Ensure that the db's internal sequence counter is > 1.

    This is used to test the `reset_sequences` feature.
    """
    item_1 = Item.objects.create(name="item_1")
    item_2 = Item.objects.create(name="item_2")
    item_1.delete()
    item_2.delete()


class TestDatabaseFixtures:
    """Tests for the different database fixtures."""

    @pytest.fixture(
        params=[
            "db",
            "transactional_db",
            "django_db_reset_sequences",
            "django_db_serialized_rollback",
        ]
    )
    def all_dbs(self, request: pytest.FixtureRequest) -> None:
        if request.param == "django_db_reset_sequences":
            request.getfixturevalue("django_db_reset_sequences")
        elif request.param == "transactional_db":
            request.getfixturevalue("transactional_db")
        elif request.param == "db":
            request.getfixturevalue("db")
        elif request.param == "django_db_serialized_rollback":
            request.getfixturevalue("django_db_serialized_rollback")
        else:
            raise AssertionError()  # pragma: no cover

    def test_access(self, all_dbs: None) -> None:
        Item.objects.create(name="spam")

    def test_clean_db(self, all_dbs: None) -> None:
        # Relies on the order: test_access created an object
        assert Item.objects.count() == 0

    def test_transactions_disabled(self, db: None) -> None:
        if not connection.features.supports_transactions:
            pytest.skip("transactions required for this test")

        assert connection.in_atomic_block

    def test_transactions_enabled(self, transactional_db: None) -> None:
        if not connection.features.supports_transactions:
            pytest.skip("transactions required for this test")

        assert not connection.in_atomic_block

    def test_transactions_enabled_via_reset_seq(
        self,
        django_db_reset_sequences: None,
    ) -> None:
        if not connection.features.supports_transactions:
            pytest.skip("transactions required for this test")

        assert not connection.in_atomic_block

    def test_django_db_reset_sequences_fixture(
        self,
        db: None,
        django_pytester: DjangoPytester,
        non_zero_sequences_counter: None,
    ) -> None:
        if not db_supports_reset_sequences():
            pytest.skip(
                "transactions and reset_sequences must be supported "
                "by the database to run this test"
            )

        # The test runs on a database that already contains objects, so its
        # id counter is > 1. We check for the ids of newly created objects.
        django_pytester.create_test_module(
            """
            import pytest
            from .app.models import Item

            def test_django_db_reset_sequences_requested(
                    django_db_reset_sequences):
                item = Item.objects.create(name='new_item')
                assert item.id == 1
        """
        )

        result = django_pytester.runpytest_subprocess("-v", "--reuse-db")
        result.stdout.fnmatch_lines(["*test_django_db_reset_sequences_requested PASSED*"])

    def test_serialized_rollback(self, db: None, django_pytester: DjangoPytester) -> None:
        django_pytester.create_app_file(
            """
            from django.db import migrations

            def load_data(apps, schema_editor):
                Item = apps.get_model("app", "Item")
                Item.objects.create(name="loaded-in-migration")

            class Migration(migrations.Migration):
                dependencies = [
                    ("app", "0001_initial"),
                ]

                operations = [
                    migrations.RunPython(load_data),
                ]
            """,
            "migrations/0002_data_migration.py",
        )

        django_pytester.create_test_module(
            """
            import pytest
            from .app.models import Item

            @pytest.mark.django_db(transaction=True, serialized_rollback=True)
            def test_serialized_rollback_1():
                assert Item.objects.filter(name="loaded-in-migration").exists()

            @pytest.mark.django_db(transaction=True)
            def test_serialized_rollback_2(django_db_serialized_rollback):
                assert Item.objects.filter(name="loaded-in-migration").exists()
                Item.objects.create(name="test2")

            @pytest.mark.django_db(transaction=True, serialized_rollback=True)
            def test_serialized_rollback_3():
                assert Item.objects.filter(name="loaded-in-migration").exists()
                assert not Item.objects.filter(name="test2").exists()
            """
        )

        result = django_pytester.runpytest_subprocess("-v")
        assert result.ret == 0

    @pytest.fixture
    def mydb(self, all_dbs: None) -> None:
        # This fixture must be able to access the database
        Item.objects.create(name="spam")

    def test_mydb(self, mydb: None) -> None:
        if not connection.features.supports_transactions:
            pytest.skip("transactions required for this test")

        # Check the fixture had access to the db
        item = Item.objects.get(name="spam")
        assert item

    def test_fixture_clean(self, all_dbs: None) -> None:
        # Relies on the order: test_mydb created an object
        # See https://github.com/pytest-dev/pytest-django/issues/17
        assert Item.objects.count() == 0

    @pytest.fixture
    def fin(self, request: pytest.FixtureRequest, all_dbs: None) -> Generator[None, None, None]:
        # This finalizer must be able to access the database
        yield
        Item.objects.create(name="spam")

    def test_fin(self, fin: None) -> None:
        # Check finalizer has db access (teardown will fail if not)
        pass

    def test_durable_transactions(self, all_dbs: None) -> None:
        with transaction.atomic(durable=True):
            item = Item.objects.create(name="foo")
        assert Item.objects.get() == item


class TestDatabaseFixturesAllOrder:
    @pytest.fixture
    def fixture_with_db(self, db: None) -> None:
        Item.objects.create(name="spam")

    @pytest.fixture
    def fixture_with_transdb(self, transactional_db: None) -> None:
        Item.objects.create(name="spam")

    @pytest.fixture
    def fixture_with_reset_sequences(self, django_db_reset_sequences: None) -> None:
        Item.objects.create(name="spam")

    @pytest.fixture
    def fixture_with_serialized_rollback(self, django_db_serialized_rollback: None) -> None:
        Item.objects.create(name="ham")

    def test_trans(self, fixture_with_transdb: None) -> None:
        pass

    def test_db(self, fixture_with_db: None) -> None:
        pass

    def test_db_trans(self, fixture_with_db: None, fixture_with_transdb: None) -> None:
        pass

    def test_trans_db(self, fixture_with_transdb: None, fixture_with_db: None) -> None:
        pass

    def test_reset_sequences(
        self,
        fixture_with_reset_sequences: None,
        fixture_with_transdb: None,
        fixture_with_db: None,
    ) -> None:
        pass

    # The test works when transactions are not supported, but it interacts
    # badly with other tests.
    @pytest.mark.skipif("not connection.features.supports_transactions")
    def test_serialized_rollback(
        self,
        fixture_with_serialized_rollback: None,
        fixture_with_db: None,
    ) -> None:
        pass


class TestDatabaseMarker:
    "Tests for the django_db marker."

    @pytest.mark.django_db
    def test_access(self) -> None:
        Item.objects.create(name="spam")

    @pytest.mark.django_db
    def test_clean_db(self) -> None:
        # Relies on the order: test_access created an object.
        assert Item.objects.count() == 0

    @pytest.mark.django_db
    def test_transactions_disabled(self) -> None:
        if not connection.features.supports_transactions:
            pytest.skip("transactions required for this test")

        assert connection.in_atomic_block

    @pytest.mark.django_db(transaction=False)
    def test_transactions_disabled_explicit(self) -> None:
        if not connection.features.supports_transactions:
            pytest.skip("transactions required for this test")

        assert connection.in_atomic_block

    @pytest.mark.django_db(transaction=True)
    def test_transactions_enabled(self) -> None:
        if not connection.features.supports_transactions:
            pytest.skip("transactions required for this test")

        assert not connection.in_atomic_block

    @pytest.mark.django_db
    def test_reset_sequences_disabled(self, request: pytest.FixtureRequest) -> None:
        marker = request.node.get_closest_marker("django_db")
        assert not marker.kwargs

    @pytest.mark.django_db(reset_sequences=True)
    def test_reset_sequences_enabled(self, request: pytest.FixtureRequest) -> None:
        marker = request.node.get_closest_marker("django_db")
        assert marker.kwargs["reset_sequences"]

    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_transaction_reset_sequences_enabled(self, request: pytest.FixtureRequest) -> None:
        marker = request.node.get_closest_marker("django_db")
        assert marker.kwargs["reset_sequences"]

    @pytest.mark.django_db(databases=["default", "replica", "second"])
    def test_databases(self, request: pytest.FixtureRequest) -> None:
        marker = request.node.get_closest_marker("django_db")
        assert marker.kwargs["databases"] == ["default", "replica", "second"]

    @pytest.mark.django_db(databases=["second"])
    def test_second_database(self, request: pytest.FixtureRequest) -> None:
        SecondItem.objects.create(name="spam")

    @pytest.mark.django_db(databases=["default"])
    def test_not_allowed_database(self, request: pytest.FixtureRequest) -> None:
        with pytest.raises(AssertionError, match="not allowed"):
            SecondItem.objects.count()
        with pytest.raises(AssertionError, match="not allowed"):
            SecondItem.objects.create(name="spam")

    @pytest.mark.django_db(databases=["replica"])
    def test_replica_database(self, request: pytest.FixtureRequest) -> None:
        Item.objects.using("replica").count()

    @pytest.mark.django_db(databases=["replica"])
    def test_replica_database_not_allowed(self, request: pytest.FixtureRequest) -> None:
        with pytest.raises(AssertionError, match="not allowed"):
            Item.objects.count()

    @pytest.mark.django_db(transaction=True, databases=["default", "replica"])
    def test_replica_mirrors_default_database(self, request: pytest.FixtureRequest) -> None:
        Item.objects.create(name="spam")
        Item.objects.using("replica").create(name="spam")

        assert Item.objects.count() == 2
        assert Item.objects.using("replica").count() == 2

    @pytest.mark.django_db(databases="__all__")
    def test_all_databases(self, request: pytest.FixtureRequest) -> None:
        Item.objects.count()
        Item.objects.create(name="spam")
        SecondItem.objects.count()
        SecondItem.objects.create(name="spam")

    @pytest.mark.django_db
    def test_serialized_rollback_disabled(self, request: pytest.FixtureRequest):
        marker = request.node.get_closest_marker("django_db")
        assert not marker.kwargs

    # The test works when transactions are not supported, but it interacts
    # badly with other tests.
    @pytest.mark.skipif("not connection.features.supports_transactions")
    @pytest.mark.django_db(serialized_rollback=True)
    def test_serialized_rollback_enabled(self, request: pytest.FixtureRequest):
        marker = request.node.get_closest_marker("django_db")
        assert marker.kwargs["serialized_rollback"]

    @pytest.mark.django_db
    def test_available_apps_disabled(self, request: pytest.FixtureRequest) -> None:
        marker = request.node.get_closest_marker("django_db")
        assert not marker.kwargs

    @pytest.mark.django_db(available_apps=["pytest_django_test.app"])
    def test_available_apps_enabled(self, request: pytest.FixtureRequest) -> None:
        marker = request.node.get_closest_marker("django_db")
        assert marker.kwargs["available_apps"] == ["pytest_django_test.app"]

    @pytest.mark.django_db
    def test_available_apps_default(self, request: pytest.FixtureRequest) -> None:
        from django.apps import apps
        from django.conf import settings

        for app in settings.INSTALLED_APPS:
            assert apps.is_installed(app)

    @pytest.mark.django_db(available_apps=["pytest_django_test.app"])
    def test_available_apps_limited(self, request: pytest.FixtureRequest) -> None:
        from django.apps import apps
        from django.conf import settings

        assert apps.is_installed("pytest_django_test.app")

        for app in settings.INSTALLED_APPS:
            if app != "pytest_django_test.app":
                assert not apps.is_installed(app)


def test_unittest_interaction(django_pytester: DjangoPytester) -> None:
    "Test that (non-Django) unittests cannot access the DB."

    django_pytester.create_test_module(
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

    result = django_pytester.runpytest_subprocess("-v", "--reuse-db")
    result.stdout.fnmatch_lines(
        [
            "*test_db_access_1 ERROR*",
            "*test_db_access_2 FAILED*",
            "*test_db_access_3 FAILED*",
            "*ERROR at setup of TestCase_setupClass.test_db_access_1*",
            '*RuntimeError: Database access not allowed, use the "django_db" mark, '
            'or the "db" or "transactional_db" fixtures to enable it.',
        ]
    )


class Test_database_blocking:
    def test_db_access_in_conftest(self, django_pytester: DjangoPytester) -> None:
        """Make sure database access in conftest module is prohibited."""

        django_pytester.makeconftest(
            """
            from tpkg.app.models import Item
            Item.objects.get()
        """
        )

        result = django_pytester.runpytest_subprocess("-v")
        result.stderr.fnmatch_lines(
            [
                '*RuntimeError: Database access not allowed, use the "django_db" mark, '
                'or the "db" or "transactional_db" fixtures to enable it.*'
            ]
        )

    def test_db_access_in_test_module(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
            from tpkg.app.models import Item
            Item.objects.get()
        """
        )

        result = django_pytester.runpytest_subprocess("-v")
        result.stdout.fnmatch_lines(
            [
                '*RuntimeError: Database access not allowed, use the "django_db" mark, '
                'or the "db" or "transactional_db" fixtures to enable it.'
            ]
        )
