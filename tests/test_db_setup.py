import pytest

from pytest_django.lazy_django import get_django_version
from pytest_django_test.db_helpers import (db_exists, drop_database,
                                           mark_database, mark_exists,
                                           skip_if_sqlite_in_memory)


def test_db_reuse_simple(django_testdir):
    "A test for all backends to check that `--reuse-db` works."
    django_testdir.create_test_module('''
        import pytest

        from .app.models import Item

        @pytest.mark.django_db
        def test_db_can_be_accessed():
            assert Item.objects.count() == 0
    ''')

    result = django_testdir.runpytest_subprocess('-v', '--reuse-db')
    assert result.ret == 0
    result.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])


def test_db_reuse(django_testdir):
    """
    Test the re-use db functionality.
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
    result_first = django_testdir.runpytest_subprocess('-v', '--reuse-db')
    assert result_first.ret == 0

    result_first.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])

    assert not mark_exists()
    mark_database()
    assert mark_exists()

    result_second = django_testdir.runpytest_subprocess('-v', '--reuse-db')
    assert result_second.ret == 0
    result_second.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])

    # Make sure the database has not been re-created
    assert mark_exists()

    result_third = django_testdir.runpytest_subprocess('-v', '--reuse-db', '--create-db')
    assert result_third.ret == 0
    result_third.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])

    # Make sure the database has been re-created and the mark is gone
    assert db_exists()
    assert not mark_exists()


class TestSqlite:

    db_settings = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db_name',
        'TEST': {
            'NAME': 'test_custom_db_name'
        }
    }}

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
                assert conn.settings_dict['NAME'] == 'test_custom_db_name'
        ''')

        result = django_testdir.runpytest_subprocess('--tb=short', '-v')
        assert result.ret == 0
        result.stdout.fnmatch_lines(['*test_a*PASSED*'])


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

    result = django_testdir.runpytest_subprocess('-vv', '-n2', '-s', '--reuse-db')
    assert result.ret == 0
    result.stdout.fnmatch_lines(['*PASSED*test_a*'])
    result.stdout.fnmatch_lines(['*PASSED*test_b*'])
    result.stdout.fnmatch_lines(['*PASSED*test_c*'])
    result.stdout.fnmatch_lines(['*PASSED*test_d*'])

    assert db_exists('gw0')
    assert db_exists('gw1')

    result = django_testdir.runpytest_subprocess('-vv', '-n2', '-s', '--reuse-db')
    assert result.ret == 0
    result.stdout.fnmatch_lines(['*PASSED*test_a*'])
    result.stdout.fnmatch_lines(['*PASSED*test_b*'])
    result.stdout.fnmatch_lines(['*PASSED*test_c*'])
    result.stdout.fnmatch_lines(['*PASSED*test_d*'])

    result = django_testdir.runpytest_subprocess('-vv', '-n2', '-s', '--reuse-db',
                                                 '--create-db')
    assert result.ret == 0
    result.stdout.fnmatch_lines(['*PASSED*test_a*'])
    result.stdout.fnmatch_lines(['*PASSED*test_b*'])
    result.stdout.fnmatch_lines(['*PASSED*test_c*'])
    result.stdout.fnmatch_lines(['*PASSED*test_d*'])


class TestSqliteWithXdist:

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
                db_name = conn.creation._get_test_db_name()
                assert 'file:memorydb' in db_name or db_name == ':memory:'
        ''')

        result = django_testdir.runpytest_subprocess('--tb=short', '-vv', '-n1')
        assert result.ret == 0
        result.stdout.fnmatch_lines(['*PASSED*test_a*'])


@pytest.mark.skipif(get_django_version() >= (1, 9),
                    reason=('Django 1.9 requires migration and has no concept '
                            'of initial data fixtures'))
def test_initial_data(django_testdir_initial):
    """Test that initial data gets loaded."""
    django_testdir_initial.create_test_module('''
        import pytest

        from .app.models import Item

        @pytest.mark.django_db
        def test_inner():
            assert [x.name for x in Item.objects.all()] \
                == ["mark_initial_data"]
    ''')

    result = django_testdir_initial.runpytest_subprocess('--tb=short', '-v')
    assert result.ret == 0
    result.stdout.fnmatch_lines(['*test_inner*PASSED*'])


class TestNativeMigrations(object):
    """ Tests for Django Migrations """

    def test_no_migrations(self, django_testdir):
        django_testdir.create_test_module('''
            import pytest

            @pytest.mark.django_db
            def test_inner_migrations():
                pass
        ''')

        migration_file = django_testdir.project_root.join("tpkg/app/migrations/0001_initial.py")
        assert migration_file.isfile()
        migration_file.write('raise Exception("This should not get imported.")', ensure=True)

        result = django_testdir.runpytest_subprocess('--nomigrations', '--tb=short', '-v')
        assert result.ret == 0
        result.stdout.fnmatch_lines(['*test_inner_migrations*PASSED*'])

    def test_migrations_run(self, django_testdir):
        testdir = django_testdir
        testdir.create_test_module('''
            import pytest

            @pytest.mark.django_db
            def test_inner_migrations():
                pass
            ''')

        testdir.create_app_file("""
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
                    migrations.RunPython(
                        print_it,
                    ),
                ]
            """, 'migrations/0001_initial.py')
        result = testdir.runpytest_subprocess('--tb=short', '-v', '-s')
        assert result.ret == 0
        result.stdout.fnmatch_lines(['*mark_migrations_run*'])

        result = testdir.runpytest_subprocess('--no-migrations', '--migrations',
                                              '--tb=short', '-v', '-s')
        assert result.ret == 0
        result.stdout.fnmatch_lines(['*mark_migrations_run*'])
