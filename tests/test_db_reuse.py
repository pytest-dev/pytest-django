import copy

import py

from django.conf import settings


TESTS = '''
from app.models import Item

def test_db_can_be_accessed():
    assert Item.objects.count() == 0
'''

import shutil

TESTS_DIR = py.path.local(__file__)


def test_db_reuse(testdir, monkeypatch):
    """
    Test the re-use db functionality. This test requires a PostgreSQL server
    to be available and the environment variables PG_HOST, PG_DB, PG_USER to
    be defined.
    """

    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
        py.test.skip('Do not test db reuse since database does not support it')

    db_settings = copy.deepcopy(settings.DATABASES)
    db_settings['default']['NAME'] = 'pytest_django_reuse'

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
    result_first = testdir.runpytest('-v', '--reuse-db', '--create-db')

    result_first.stdout.fnmatch_lines([
        "Creating test database for alias 'default'...",
    ])

    result_first.stdout.fnmatch_lines([
        "*test_db_can_be_accessed PASSED*",
    ])

    assert result_first.ret == 0

    result_second = testdir.runpytest('-v', '--reuse-db')

    result_second.stdout.fnmatch_lines([
        "Re-using existing test database for alias 'default'...",
    ])

    assert result_second.ret == 0

    result_third = testdir.runpytest('-v', '--reuse-db', '--create-db')

    result_third.stdout.fnmatch_lines([
        "Creating test database for alias 'default'...",
    ])

    assert result_third.ret == 0
