import copy

import py
import pytest

envoy = pytest.importorskip('envoy')

from django.conf import settings


import shutil

TESTS_DIR = py.path.local(__file__)

DB_NAME = 'pytest_django_db_test'
TEST_DB_NAME = 'test_' + DB_NAME
ENGINE = settings.DATABASES['default']['ENGINE'].split('.')[-1]


def create_empty_production_database():
    drop_database(name=DB_NAME)

    if ENGINE == 'postgresql_psycopg2':
        r = envoy.run('echo CREATE DATABASE %s | psql postgres' % DB_NAME)
        assert 'CREATE DATABASE' in r.std_out or 'already exists' in r.std_err
        return

    if ENGINE == 'mysql':
        r = envoy.run('echo CREATE DATABASE %s | mysql' % DB_NAME)
        assert r.status_code == 0 or 'database exists' in r.std_out
        return

    raise AssertionError('%s cannot be tested properly' % ENGINE)


def drop_database(name=TEST_DB_NAME):
    if ENGINE == 'postgresql_psycopg2':
        r = envoy.run('echo DROP DATABASE %s | psql postgres' % name)
        assert r.status_code == 0
        assert 'DROP DATABASE' in r.std_out or 'does not exist' in r.std_err
        return

    if ENGINE == 'mysql':
        r = envoy.run('echo DROP DATABASE %s | mysql -u root' % name)
        assert ('database doesn\'t exist' in r.std_err
                or r.status_code == 0)
        return

    raise AssertionError('%s cannot be tested properly!' % ENGINE)


def db_exists():
    if ENGINE == 'postgresql_psycopg2':
        r = envoy.run('echo SELECT 1 | psql %s' % TEST_DB_NAME)
        return r.status_code == 0

    if ENGINE == 'mysql':
        r = envoy.run('echo SELECT 1 | mysql %s' % TEST_DB_NAME)
        return r.status_code == 0

    raise AssertionError('%s cannot be tested properly!' % ENGINE)


def mark_database():
    if ENGINE == 'postgresql_psycopg2':
        r = envoy.run('echo CREATE TABLE mark_table(); | psql %s' % TEST_DB_NAME)
        assert r.status_code == 0
        return

    if ENGINE == 'mysql':
        r = envoy.run('echo CREATE TABLE mark_table(kaka int); | mysql %s' % TEST_DB_NAME)
        assert r.status_code == 0
        return

    raise AssertionError('%s cannot be tested properly!' % ENGINE)


def mark_exists():
    if ENGINE == 'postgresql_psycopg2':
        f = envoy.run('echo SELECT 1 FROM mark_table | psql %s' % TEST_DB_NAME)
        assert f.status_code == 0

        # When something pops out on std_out, we are good
        return bool(f.std_out)

    if ENGINE == 'mysql':
        f = envoy.run('echo SELECT 1 FROM mark_table | mysql %s' % TEST_DB_NAME)
        return f.status_code == 0

    raise AssertionError('%s cannot be tested properly!' % ENGINE)


def setup_test_environ(testdir, monkeypatch, test_code):
    if ENGINE in ('mysql', 'postgresql_psycopg2'):
        # Django requires the production database to exists..
        create_empty_production_database()

    db_settings = copy.deepcopy(settings.DATABASES)
    db_settings['default']['NAME'] = DB_NAME

    test_settings = '''
# Pypy compatibility
try:
    from psycopg2ct import compat
except ImportError:
    pass
else:
    compat.register()

DATABASES = %(db_settings)s

INSTALLED_APPS = [
    'tpkg.app',
]

''' % {'db_settings': repr(db_settings)}

    tpkg_path = testdir.mkpydir('tpkg')
    app_source = TESTS_DIR.dirpath('app')

    # Copy the test app to make it available in the new test run
    shutil.copytree(unicode(app_source), unicode(tpkg_path.join('app')))

    tpkg_path.join("test_the_actual_tests.py").write(test_code)
    tpkg_path.join("db_test_settings.py").write(test_settings)

    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.db_test_settings')

    return tpkg_path


def test_django_testcase_setup(testdir, monkeypatch):
    """
    Make sure the database are configured when only Django TestCase classes
    are collected, without the django_db marker.
    """
    setup_test_environ(testdir, monkeypatch, '''
from django.test import TestCase
from django.conf import settings

from app.models import Item

class TestFoo(TestCase):
    def test_foo(self):
        # Make sure we are actually using the test database
        db_name = settings.DATABASES['default']['NAME']
        assert db_name.startswith('test_') or db_name == ':memory:'

        # Make sure it is usable
        assert Item.objects.count() == 0

''')

    result = testdir.runpytest('-v')
    result.stdout.fnmatch_lines([
        "*TestFoo.test_foo PASSED*",
    ])


def test_db_reuse(testdir, monkeypatch):
    """
    Test the re-use db functionality. This test requires a PostgreSQL server
    to be available and the environment variables PG_HOST, PG_DB, PG_USER to
    be defined.
    """

    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
        py.test.skip('Do not test db reuse since database does not support it')

    setup_test_environ(testdir, monkeypatch, '''
import pytest

from app.models import Item

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
    result_first = testdir.runpytest('-v', '--reuse-db')

    result_first.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])

    assert not mark_exists()
    mark_database()
    assert mark_exists()

    result_second = testdir.runpytest('-v', '--reuse-db')
    result_second.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])

    # Make sure the database has not been re-created
    assert mark_exists()

    result_third = testdir.runpytest('-v', '--reuse-db', '--create-db')
    result_third.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])

    # Make sure the database has been re-created and the mark is gone
    assert not mark_exists()

# def test_conftest_connection_caching(testdir, monkeypatch):
#     """
#     Make sure django.db.connections is properly cleared before a @django_db
#     test, when a connection to the actual database has been constructed.

#     """
#     tpkg_path = setup_test_environ(testdir, monkeypatch, '''
# import pytest

# from django.test import TestCase
# from django.conf import settings

# from app.models import Item

# def test_a():
#     # assert settings.DATABASES['default']['NAME'] == 'test_pytest_django_db_testasdf'
#     Item.objects.count()

# @pytest.mark.django_db
# def test_b():
#     assert settings.DATABASES['default']['NAME'] == 'test_pytest_django_db_test'
#     Item.objects.count()

# ''')

#     tpkg_path.join('conftest.py').write('''
# # from app.models import Item
# # Item.objects.count()
# # from django.db import models
# from django.db import connection
# cursor = connection.cursor()
# cursor.execute('SELECT 1')


# ''')
    # result = testdir.runpytest('-v')
    # result.stdout.fnmatch_lines([
    #     "*test_b PASSED*",
    #     "*test_a PASSED*",
    # ])
