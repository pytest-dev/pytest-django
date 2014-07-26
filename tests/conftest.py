import pytest
import py

import shutil
import copy
from textwrap import dedent


pytest_plugins = 'pytester'

TESTS_DIR = py.path.local(__file__)


from django.conf import settings


# Trigger loading of Django settings, which might raise pytest.UsageError.
from .db_helpers import (create_empty_production_database, get_db_engine,
                         DB_NAME)


@pytest.fixture(scope='function')
def django_testdir(request, testdir, monkeypatch):
    if get_db_engine() in ('mysql', 'postgresql_psycopg2', 'sqlite3'):
        # Django requires the production database to exists..
        create_empty_production_database()

    if hasattr(request.node.cls, 'db_settings'):
        db_settings = request.node.cls.db_settings
    else:
        db_settings = copy.deepcopy(settings.DATABASES)
        db_settings['default']['NAME'] = DB_NAME

    extra_settings = request.node.get_marker('extra_settings') or ''
    if extra_settings:
        extra_settings = extra_settings.args[0]
    test_settings = dedent('''
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
        SECRET_KEY = 'foobar'

        %(extra_settings)s
    ''') % {'db_settings': repr(db_settings), 'extra_settings': extra_settings}

    tpkg_path = testdir.mkpydir('tpkg')
    app_source = TESTS_DIR.dirpath('app')
    test_app_path = tpkg_path.join('app')

    # Copy the test app to make it available in the new test run
    shutil.copytree(py.builtin._totext(app_source),
                    py.builtin._totext(test_app_path))
    tpkg_path.join("db_test_settings.py").write(test_settings)

    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.db_test_settings')

    def create_test_module(test_code, filename='test_the_test.py'):
        tpkg_path = testdir.tmpdir / 'tpkg'
        tpkg_path.join(filename).write(dedent(test_code))

    def create_app_file(code, filename):
        test_app_path.join(filename).write(dedent(code))

    testdir.create_test_module = create_test_module
    testdir.create_app_file = create_app_file

    return testdir
