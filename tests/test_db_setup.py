from __future__ import annotations

from typing import ClassVar

import pytest

from .helpers import DjangoPytester

from pytest_django_test.db_helpers import (
    db_exists,
    drop_database,
    mark_database,
    mark_exists,
    skip_if_sqlite_in_memory,
)


def test_db_reuse_simple(django_pytester: DjangoPytester) -> None:
    "A test for all backends to check that `--reuse-db` works."
    django_pytester.create_test_module(
        """
        import pytest

        from .app.models import Item

        @pytest.mark.django_db
        def test_db_can_be_accessed():
            assert Item.objects.count() == 0
    """
    )

    result = django_pytester.runpytest_subprocess("-v", "--reuse-db")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*test_db_can_be_accessed PASSED*"])


def test_db_order(django_pytester: DjangoPytester) -> None:
    """Test order in which tests are being executed."""

    django_pytester.create_test_module(
        """
        import pytest
        from unittest import TestCase
        from django.test import SimpleTestCase
        from django.test import TestCase as DjangoTestCase
        from django.test import TransactionTestCase

        from .app.models import Item

        @pytest.mark.django_db(transaction=True)
        def test_run_second_decorator():
            pass

        def test_run_second_fixture(transactional_db):
            pass

        def test_run_second_reset_sequences_fixture(django_db_reset_sequences):
            pass

        class MyTransactionTestCase(TransactionTestCase):
            def test_run_second_transaction_test_case(self):
                pass

        def test_run_first_fixture(db):
            pass

        class TestClass:
            def test_run_second_fixture_class(self, transactional_db):
                pass

            def test_run_first_fixture_class(self, db):
                pass

        @pytest.mark.django_db(reset_sequences=True)
        def test_run_second_reset_sequences_decorator():
            pass

        class MyDjangoTestCase(DjangoTestCase):
            def test_run_first_django_test_case(self):
                pass

        class MySimpleTestCase(SimpleTestCase):
            def test_run_last_simple_test_case(self):
                pass

        @pytest.mark.django_db
        def test_run_first_decorator():
            pass

        @pytest.mark.django_db(serialized_rollback=True)
        def test_run_first_serialized_rollback_decorator():
            pass

        class MyTestCase(TestCase):
            def test_run_last_test_case(self):
                pass
    """
    )
    result = django_pytester.runpytest_subprocess("-q", "--collect-only")
    assert result.ret == 0
    result.stdout.fnmatch_lines(
        [
            "*test_run_first_fixture*",
            "*test_run_first_fixture_class*",
            "*test_run_first_django_test_case*",
            "*test_run_first_decorator*",
            "*test_run_first_serialized_rollback_decorator*",
            "*test_run_second_decorator*",
            "*test_run_second_fixture*",
            "*test_run_second_reset_sequences_fixture*",
            "*test_run_second_transaction_test_case*",
            "*test_run_second_fixture_class*",
            "*test_run_second_reset_sequences_decorator*",
            "*test_run_last_simple_test_case*",
            "*test_run_last_test_case*",
        ],
        consecutive=True,
    )


def test_db_reuse(django_pytester: DjangoPytester) -> None:
    """
    Test the re-use db functionality.
    """
    skip_if_sqlite_in_memory()

    django_pytester.create_test_module(
        """
        import pytest

        from .app.models import Item

        @pytest.mark.django_db
        def test_db_can_be_accessed():
            assert Item.objects.count() == 0
    """
    )

    # Use --create-db on the first run to make sure we are not just re-using a
    # database from another test run
    drop_database()
    assert not db_exists()

    # Do not pass in --create-db to make sure it is created when it
    # does not exist
    result_first = django_pytester.runpytest_subprocess("-v", "--reuse-db")
    assert result_first.ret == 0

    result_first.stdout.fnmatch_lines(["*test_db_can_be_accessed PASSED*"])

    assert not mark_exists()
    mark_database()
    assert mark_exists()

    result_second = django_pytester.runpytest_subprocess("-v", "--reuse-db")
    assert result_second.ret == 0
    result_second.stdout.fnmatch_lines(["*test_db_can_be_accessed PASSED*"])

    # Make sure the database has not been re-created
    assert mark_exists()

    result_third = django_pytester.runpytest_subprocess("-v", "--reuse-db", "--create-db")
    assert result_third.ret == 0
    result_third.stdout.fnmatch_lines(["*test_db_can_be_accessed PASSED*"])

    # Make sure the database has been re-created and the mark is gone
    assert db_exists()
    assert not mark_exists()


class TestSqlite:
    db_settings: ClassVar = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "db_name",
            "TEST": {"NAME": "test_custom_db_name"},
        }
    }

    def test_sqlite_test_name_used(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
            import pytest
            from django.db import connections
            from django import VERSION

            @pytest.mark.django_db
            def test_a():
                (conn, ) = connections.all()

                assert conn.vendor == 'sqlite'
                print(conn.settings_dict)
                assert conn.settings_dict['NAME'] == 'test_custom_db_name'
        """
        )

        result = django_pytester.runpytest_subprocess("--tb=short", "-v")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*test_a*PASSED*"])


def test_xdist_with_reuse(django_pytester: DjangoPytester) -> None:
    pytest.importorskip("xdist")
    skip_if_sqlite_in_memory()

    drop_database("gw0")
    drop_database("gw1")
    assert not db_exists("gw0")
    assert not db_exists("gw1")

    django_pytester.create_test_module(
        """
        import pytest

        from .app.models import Item

        def _check(settings):
            # Make sure that the database name looks correct
            db_name = settings.DATABASES['default']['NAME']
            assert db_name.endswith('_gw0') or db_name.endswith('_gw1')

            assert Item.objects.count() == 0
            Item.objects.create(name='foo')
            assert Item.objects.count() == 1


        @pytest.mark.django_db
        def test_a(settings):
            _check(settings)


        @pytest.mark.django_db
        def test_b(settings):
            _check(settings)

        @pytest.mark.django_db
        def test_c(settings):
            _check(settings)

        @pytest.mark.django_db
        def test_d(settings):
            _check(settings)
    """
    )

    result = django_pytester.runpytest_subprocess("-vv", "-n2", "-s", "--reuse-db")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*PASSED*test_a*"])
    result.stdout.fnmatch_lines(["*PASSED*test_b*"])
    result.stdout.fnmatch_lines(["*PASSED*test_c*"])
    result.stdout.fnmatch_lines(["*PASSED*test_d*"])

    assert db_exists("gw0")
    assert db_exists("gw1")

    result = django_pytester.runpytest_subprocess("-vv", "-n2", "-s", "--reuse-db")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*PASSED*test_a*"])
    result.stdout.fnmatch_lines(["*PASSED*test_b*"])
    result.stdout.fnmatch_lines(["*PASSED*test_c*"])
    result.stdout.fnmatch_lines(["*PASSED*test_d*"])

    result = django_pytester.runpytest_subprocess("-vv", "-n2", "-s", "--reuse-db", "--create-db")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*PASSED*test_a*"])
    result.stdout.fnmatch_lines(["*PASSED*test_b*"])
    result.stdout.fnmatch_lines(["*PASSED*test_c*"])
    result.stdout.fnmatch_lines(["*PASSED*test_d*"])

    # Cleanup.
    drop_database("gw0")
    drop_database("gw1")


class TestSqliteWithXdist:
    db_settings: ClassVar = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "/tmp/should-not-be-used",
        }
    }

    def test_sqlite_in_memory_used(self, django_pytester: DjangoPytester) -> None:
        pytest.importorskip("xdist")

        django_pytester.create_test_module(
            """
            import pytest
            from django.db import connections

            @pytest.mark.django_db
            def test_a():
                (conn, ) = connections.all()

                assert conn.vendor == 'sqlite'
                db_name = conn.creation._get_test_db_name()
                assert 'file:memorydb' in db_name or db_name == ':memory:'
        """
        )

        result = django_pytester.runpytest_subprocess("--tb=short", "-vv", "-n1")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*PASSED*test_a*"])


class TestSqliteWithMultipleDbsAndXdist:
    db_settings: ClassVar = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "/tmp/should-not-be-used",
        },
        "db2": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "db_name",
            "TEST": {"NAME": "test_custom_db_name"},
        },
    }

    def test_sqlite_database_renamed(self, django_pytester: DjangoPytester) -> None:
        pytest.importorskip("xdist")

        django_pytester.create_test_module(
            """
            import pytest
            from django.db import connections

            @pytest.mark.django_db
            def test_a():
                (conn_db2, conn_default) = sorted(
                    connections.all(),
                    key=lambda conn: conn.alias,
                )

                assert conn_default.vendor == 'sqlite'
                db_name = conn_default.creation._get_test_db_name()

                # can_share_in_memory_db was removed in Django 2.1, and
                # used in _get_test_db_name before.
                if getattr(conn_default.features, "can_share_in_memory_db", True):
                    assert 'file:memorydb' in db_name
                else:
                    assert db_name == ":memory:"

                assert conn_db2.vendor == 'sqlite'
                db_name = conn_db2.creation._get_test_db_name()
                assert db_name.startswith('test_custom_db_name_gw')
        """
        )

        result = django_pytester.runpytest_subprocess("--tb=short", "-vv", "-n1")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*PASSED*test_a*"])


class TestSqliteWithTox:
    db_settings: ClassVar = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "db_name",
            "TEST": {"NAME": "test_custom_db_name"},
        }
    }

    def test_db_with_tox_suffix(
        self,
        django_pytester: DjangoPytester,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        "A test to check that Tox DB suffix works when running in parallel."
        monkeypatch.setenv("TOX_PARALLEL_ENV", "py37-django22")

        django_pytester.create_test_module(
            """
            import pytest
            from django.db import connections

            @pytest.mark.django_db
            def test_inner():

                (conn, ) = connections.all()

                assert conn.vendor == 'sqlite'
                db_name = conn.creation._get_test_db_name()
                assert db_name == 'test_custom_db_name_py37-django22'
        """
        )

        result = django_pytester.runpytest_subprocess("--tb=short", "-vv")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*test_inner*PASSED*"])

    def test_db_with_empty_tox_suffix(
        self,
        django_pytester: DjangoPytester,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        "A test to check that Tox DB suffix is not used when suffix would be empty."
        monkeypatch.setenv("TOX_PARALLEL_ENV", "")

        django_pytester.create_test_module(
            """
            import pytest
            from django.db import connections

            @pytest.mark.django_db
            def test_inner():

                (conn,) = connections.all()

                assert conn.vendor == 'sqlite'
                db_name = conn.creation._get_test_db_name()
                assert db_name == 'test_custom_db_name'
        """
        )

        result = django_pytester.runpytest_subprocess("--tb=short", "-vv")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*test_inner*PASSED*"])


class TestSqliteWithToxAndXdist:
    db_settings: ClassVar = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "db_name",
            "TEST": {"NAME": "test_custom_db_name"},
        }
    }

    def test_db_with_tox_suffix(
        self,
        django_pytester: DjangoPytester,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        "A test to check that both Tox and xdist suffixes work together."
        pytest.importorskip("xdist")
        monkeypatch.setenv("TOX_PARALLEL_ENV", "py37-django22")

        django_pytester.create_test_module(
            """
            import pytest
            from django.db import connections

            @pytest.mark.django_db
            def test_inner():

                (conn, ) = connections.all()

                assert conn.vendor == 'sqlite'
                db_name = conn.creation._get_test_db_name()
                assert db_name.startswith('test_custom_db_name_py37-django22_gw')
        """
        )

        result = django_pytester.runpytest_subprocess("--tb=short", "-vv", "-n1")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*PASSED*test_inner*"])


class TestSqliteInMemoryWithXdist:
    db_settings: ClassVar = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
            "TEST": {"NAME": ":memory:"},
        }
    }

    def test_sqlite_in_memory_used(self, django_pytester: DjangoPytester) -> None:
        pytest.importorskip("xdist")

        django_pytester.create_test_module(
            """
            import pytest
            from django.db import connections

            @pytest.mark.django_db
            def test_a():
                (conn, ) = connections.all()

                assert conn.vendor == 'sqlite'
                db_name = conn.creation._get_test_db_name()
                assert 'file:memorydb' in db_name or db_name == ':memory:'
        """
        )

        result = django_pytester.runpytest_subprocess("--tb=short", "-vv", "-n1")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*PASSED*test_a*"])


class TestMigrations:
    """Tests for Django Migrations."""

    def test_no_migrations(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
            import pytest

            @pytest.mark.django_db
            def test_inner_migrations():
                from .app.models import Item
                Item.objects.create()
        """
        )

        django_pytester.create_test_module(
            """
            raise Exception("This should not get imported.")
            """,
            "migrations/0001_initial.py",
        )

        result = django_pytester.runpytest_subprocess(
            "--nomigrations",
            "--tb=short",
            "-vv",
            "-s",
        )
        assert result.ret == 0
        assert "Operations to perform:" not in result.stdout.str()
        result.stdout.fnmatch_lines(["*= 1 passed*"])

    def test_migrations_run(self, django_pytester: DjangoPytester) -> None:
        pytester = django_pytester
        pytester.create_test_module(
            """
            import pytest

            @pytest.mark.django_db
            def test_inner_migrations():
                from .app.models import Item
                Item.objects.create()
            """
        )

        pytester.create_app_file(
            """
            from django.db import migrations, models

            def print_it(apps, schema_editor):
                print("mark_migrations_run")

            class Migration(migrations.Migration):

                dependencies = []

                operations = [
                    migrations.CreateModel(
                        name='Item',
                        fields=[
                            ('id', models.AutoField(serialize=False,
                                                    auto_created=True,
                                                    primary_key=True)),
                            ('name', models.CharField(max_length=100)),
                        ],
                        options={
                        },
                        bases=(models.Model,),
                    ),
                    migrations.CreateModel(
                        name='SecondItem',
                        fields=[
                            ('id', models.AutoField(serialize=False,
                                                    auto_created=True,
                                                    primary_key=True)),
                            ('name', models.CharField(max_length=100)),
                        ],
                    ),
                    migrations.RunPython(
                        print_it,
                    ),
                ]
            """,
            "migrations/0001_initial.py",
        )
        result = pytester.runpytest_subprocess("--tb=short", "-v", "-s")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*mark_migrations_run*"])

        result = pytester.runpytest_subprocess(
            "--no-migrations", "--migrations", "--tb=short", "-v", "-s"
        )
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*mark_migrations_run*"])
