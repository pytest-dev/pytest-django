import sys

import pytest

from .db_helpers import (db_exists, drop_database, mark_database, mark_exists,
                         skip_if_sqlite_in_memory)


skip_on_python32 = pytest.mark.skipif(sys.version_info[:2] == (3, 2),
                                      reason='xdist is flaky with Python 3.2')


def test_db_reuse(django_testdir):
    """
    Test the re-use db functionality. This test requires a PostgreSQL server
    to be available and the environment variables PG_HOST, PG_DB, PG_USER to
    be defined.
    """
    skip_if_sqlite_in_memory()

    django_testdir.create_test_module('''
        import pytest

        from .app.models import Item

        @pytest.mark.django_db
        def test_db_can_be_accessed():
            assert Item.objects.count() == 0
    ''')

    # Use --create-db on the first run to make sure we are not just re-using a
    # database from another test run
    drop_database()
    assert not db_exists()

    # Do not pass in --create-db to make sure it is created when it
    # does not exist
    result_first = django_testdir.runpytest('-v', '--reuse-db')

    result_first.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])

    assert not mark_exists()
    mark_database()
    assert mark_exists()

    result_second = django_testdir.runpytest('-v', '--reuse-db')
    result_second.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])

    # Make sure the database has not been re-created
    assert mark_exists()

    result_third = django_testdir.runpytest('-v', '--reuse-db', '--create-db')
    result_third.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])

    # Make sure the database has been re-created and the mark is gone
    assert not mark_exists()


@skip_on_python32
def test_xdist_with_reuse(django_testdir):
    skip_if_sqlite_in_memory()

    drop_database('gw0')
    drop_database('gw1')

    django_testdir.create_test_module('''
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
    ''')

    result = django_testdir.runpytest('-vv', '-n2', '-s', '--reuse-db')
    result.stdout.fnmatch_lines(['*PASSED*test_a*'])
    result.stdout.fnmatch_lines(['*PASSED*test_b*'])

    assert db_exists('gw0')
    assert db_exists('gw1')

    result = django_testdir.runpytest('-vv', '-n2', '-s', '--reuse-db')
    result.stdout.fnmatch_lines(['*PASSED*test_a*'])
    result.stdout.fnmatch_lines(['*PASSED*test_b*'])

    result = django_testdir.runpytest('-vv', '-n2', '-s', '--reuse-db', '--create-db')
    result.stdout.fnmatch_lines(['*PASSED*test_a*'])
    result.stdout.fnmatch_lines(['*PASSED*test_b*'])


class TestSqliteWithXdist:

    pytestmark = skip_on_python32

    db_settings = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/should-not-be-used',
    }}

    def test_sqlite_in_memory_used(self, django_testdir):

        django_testdir.create_test_module('''
            import pytest
            from django.db import connections

            @pytest.mark.django_db
            def test_a():
                (conn, ) = connections.all()

                assert conn.vendor == 'sqlite'
                assert conn.settings_dict['NAME'] == ':memory:'
        ''')

        result = django_testdir.runpytest('--tb=short', '-vv', '-n1')
        result.stdout.fnmatch_lines(['*PASSED*test_a*'])
