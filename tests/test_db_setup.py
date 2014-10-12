import sys

import pytest

from pytest_django.lazy_django import get_django_version
from pytest_django_test.db_helpers import (db_exists, drop_database,
                                           mark_database, mark_exists,
                                           skip_if_sqlite_in_memory)

skip_on_python32 = pytest.mark.skipif(sys.version_info[:2] == (3, 2),
                                      reason='xdist is flaky with Python 3.2')


def test_db_reuse_simple(django_testdir):
    "A test for all backends to check that `--reuse-db` works."
    django_testdir.create_test_module('''
        import pytest

        from .app.models import Item

        @pytest.mark.django_db
        def test_db_can_be_accessed():
            assert Item.objects.count() == 0
    ''')

    result = django_testdir.runpytest('-v', '--reuse-db')
    result.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])


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


class TestSqlite:

    db_name_17 = 'test_db_name_django17'
    db_name_before_17 = 'test_db_name_before_django17'

    db_settings = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db_name',
    }}
    from django import VERSION
    if VERSION > (1, 7):
        db_settings['default']['TEST'] = {'NAME': db_name_17}
    else:
        db_settings['default']['TEST_NAME'] = db_name_before_17

    def test_sqlite_test_name_used(self, django_testdir):

        django_testdir.create_test_module('''
            import pytest
            from django.db import connections
            from django import VERSION

            @pytest.mark.django_db
            def test_a():
                (conn, ) = connections.all()

                assert conn.vendor == 'sqlite'
                print(conn.settings_dict)
                if VERSION > (1,7):
                    assert conn.settings_dict['NAME'] == '%s'
                else:
                    assert conn.settings_dict['NAME'] == '%s'
        ''' % (self.db_name_17, self.db_name_before_17))

        result = django_testdir.runpytest('--tb=short', '-v')
        result.stdout.fnmatch_lines(['*test_a*PASSED*'])


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

        @pytest.mark.django_db
        def test_c(settings):
            _check(settings)

        @pytest.mark.django_db
        def test_d(settings):
            _check(settings)
    ''')

    result = django_testdir.runpytest('-vv', '-n2', '-s', '--reuse-db')
    result.stdout.fnmatch_lines(['*PASSED*test_a*'])
    result.stdout.fnmatch_lines(['*PASSED*test_b*'])
    result.stdout.fnmatch_lines(['*PASSED*test_c*'])
    result.stdout.fnmatch_lines(['*PASSED*test_d*'])

    assert db_exists('gw0')
    assert db_exists('gw1')

    result = django_testdir.runpytest('-vv', '-n2', '-s', '--reuse-db')
    result.stdout.fnmatch_lines(['*PASSED*test_a*'])
    result.stdout.fnmatch_lines(['*PASSED*test_b*'])
    result.stdout.fnmatch_lines(['*PASSED*test_c*'])
    result.stdout.fnmatch_lines(['*PASSED*test_d*'])

    result = django_testdir.runpytest('-vv', '-n2', '-s', '--reuse-db',
                                      '--create-db')
    result.stdout.fnmatch_lines(['*PASSED*test_a*'])
    result.stdout.fnmatch_lines(['*PASSED*test_b*'])
    result.stdout.fnmatch_lines(['*PASSED*test_c*'])
    result.stdout.fnmatch_lines(['*PASSED*test_d*'])


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
                assert conn.creation._get_test_db_name() == ':memory:'
        ''')

        result = django_testdir.runpytest('--tb=short', '-vv', '-n1')
        result.stdout.fnmatch_lines(['*PASSED*test_a*'])


def test_initial_data(django_testdir_initial):
    """Test that initial data gets loaded."""
    django_testdir_initial.create_test_module('''
        import pytest

        from .app.models import Item

        @pytest.mark.django_db
        def test_inner_south():
            assert [x.name for x in Item.objects.all()] \
                == ["mark_initial_data"]
    ''')

    result = django_testdir_initial.runpytest('--tb=short', '-v')
    result.stdout.fnmatch_lines(['*test_inner_south*PASSED*'])


# NOTE: South tries to monkey-patch management._commands, which has been
#       replaced by lru_cache and would cause an AttributeError.
@pytest.mark.skipif(get_django_version() >= (1, 7),
                    reason='South does not support Django 1.7+')
@pytest.mark.skipif(sys.version_info[0] == 3,
                    reason='South is not properly supported on Python 3')
class TestSouth:
    """Test interaction with initial_data and South."""

    @pytest.mark.django_project(extra_settings="""
        INSTALLED_APPS += [ 'south', ]
        SOUTH_TESTS_MIGRATE = True
        SOUTH_MIGRATION_MODULES = {
            'app': 'app.south_migrations',
        }
        """)
    def test_initial_data_south(self, django_testdir_initial):
        django_testdir_initial.create_test_module('''
            import pytest

            from .app.models import Item

            @pytest.mark.django_db
            def test_inner_south():
                assert [x.name for x in Item.objects.all()] \
                    == ["mark_initial_data"]
        ''')

        result = django_testdir_initial.runpytest('--tb=short', '-v')
        result.stdout.fnmatch_lines(['*test_inner_south*PASSED*'])

    @pytest.mark.django_project(extra_settings="""
        INSTALLED_APPS += [ 'south', ]
        SOUTH_TESTS_MIGRATE = True
        SOUTH_MIGRATION_MODULES = {
            'app': 'tpkg.app.south_migrations',
        }
        """)
    def test_initial_south_migrations(self, django_testdir_initial):
        testdir = django_testdir_initial
        testdir.create_test_module('''
            import pytest

            @pytest.mark.django_db
            def test_inner_south():
                pass
            ''')

        testdir.mkpydir('tpkg/app/south_migrations')
        testdir.create_app_file("""
            from south.v2 import SchemaMigration

            class Migration(SchemaMigration):
                def forwards(self, orm):
                    print("mark_south_migration_forwards")
            """, 'south_migrations/0001_initial.py')
        result = testdir.runpytest('--tb=short', '-v', '-s')
        result.stdout.fnmatch_lines(['*mark_south_migration_forwards*'])

    @pytest.mark.django_project(extra_settings="""
        INSTALLED_APPS += [ 'south', ]
        SOUTH_TESTS_MIGRATE = False
        SOUTH_MIGRATION_MODULES = {
            'app': 'tpkg.app.south_migrations',
        }
        """)
    def test_south_no_migrations(self, django_testdir_initial):
        testdir = django_testdir_initial
        testdir.create_test_module('''
            import pytest

            @pytest.mark.django_db
            def test_inner_south():
                pass
        ''')

        testdir.mkpydir('tpkg/app/south_migrations')
        p = testdir.tmpdir.join(
            "tpkg/app/south_migrations/0001_initial").new(ext="py")
        p.write('raise Exception("This should not get imported.")',
                ensure=True)

        result = testdir.runpytest('--tb=short', '-v')
        result.stdout.fnmatch_lines(['*test_inner_south*PASSED*'])
