import copy
import envoy

import py

from django.conf import settings


TESTS = '''
import pytest

from app.models import Item

@pytest.mark.django_db
def test_db_can_be_accessed():
    assert Item.objects.count() == 0
'''

import shutil

TESTS_DIR = py.path.local(__file__)

DB_NAME = 'pytest_django_reuse'
TEST_DB_NAME = 'test_pytest_django_reuse'
ENGINE = settings.DATABASES['default']['ENGINE'].split('.')[-1]


def drop_database():
    if ENGINE == 'postgresql_psycopg2':
        r = envoy.run('echo DROP DATABASE %s | psql postgres' % TEST_DB_NAME)
        assert r.status_code == 0
        assert (r.std_err == 'ERROR:  database "%s" does not exist\n' % TEST_DB_NAME
                or r.std_out == 'DROP DATABASE\n')
        return

    raise AssertionError('%s cannot be tested properly!' % ENGINE)


def db_exists():
    if ENGINE == 'postgresql_psycopg2':
        r = envoy.run('echo SELECT 1 | psql %s' % TEST_DB_NAME)
        return r.status_code == 0

    raise AssertionError('%s cannot be tested properly!' % ENGINE)


def mark_database():
    if ENGINE == 'postgresql_psycopg2':
        r = envoy.run('echo CREATE TABLE mark_table(); | psql %s' % TEST_DB_NAME)
        assert r.status_code == 0
        return

    raise AssertionError('%s cannot be tested properly!' % ENGINE)


def mark_exists():
    if ENGINE == 'postgresql_psycopg2':
        f = envoy.run('echo SELECT 1 FROM mark_table | psql %s' % TEST_DB_NAME)
        assert f.status_code == 0

        # When something pops out on std_out, we are good
        return bool(f.std_out)

    raise AssertionError('%s cannot be tested properly!' % ENGINE)


def test_db_reuse(testdir, monkeypatch):
    """
    Test the re-use db functionality. This test requires a PostgreSQL server
    to be available and the environment variables PG_HOST, PG_DB, PG_USER to
    be defined.
    """

    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
        py.test.skip('Do not test db reuse since database does not support it')

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

    tpkg_path.join("test_db_reuse.py").write(TESTS)
    tpkg_path.join("db_reuse_settings.py").write(test_settings)

    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.db_reuse_settings')

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

    assert result_first.ret == 0
    assert not mark_exists()
    mark_database()
    assert mark_exists()

    result_second = testdir.runpytest('-v', '--reuse-db')
    result_second.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])
    assert result_second.ret == 0

    # Make sure the database has not been re-created
    assert mark_exists()

    result_third = testdir.runpytest('-v', '--reuse-db', '--create-db')
    result_third.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])
    assert result_third.ret == 0

    # Make sure the database has been re-created and the mark is gone
    assert not mark_exists()
