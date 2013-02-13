import py

from django.conf import settings

from .conftest import create_test_module
from .db_helpers import mark_exists, mark_database, drop_database, db_exists


def test_db_reuse(django_testdir):
    """
    Test the re-use db functionality. This test requires a PostgreSQL server
    to be available and the environment variables PG_HOST, PG_DB, PG_USER to
    be defined.
    """

    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
        py.test.skip('Do not test db reuse since database does not support it')

    create_test_module(django_testdir, '''
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


# def test_conftest_connection_caching(django_testdir, monkeypatch):
#     """
#     Make sure django.db.connections is properly cleared before a @django_db
#     test, when a connection to the actual database has been constructed.

#     """
#     tpkg_path = setup_test_environ(django_testdir, monkeypatch, '''
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
    # result = django_testdir.runpytest('-v')
    # result.stdout.fnmatch_lines([
    #     "*test_b PASSED*",
    #     "*test_a PASSED*",
    # ])
