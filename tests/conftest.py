import copy
import shutil
from textwrap import dedent

import py
import pytest
from django.conf import settings

from .db_helpers import (create_empty_production_database, DB_NAME,
                         get_db_engine)

pytest_plugins = 'pytester'

TESTS_DIR = py.path.local(__file__)


@pytest.fixture(scope='function')
def django_testdir(request, testdir, monkeypatch):
    db_engine = get_db_engine()
    if db_engine in ('mysql', 'postgresql_psycopg2') \
            or (db_engine == 'sqlite3' and DB_NAME != ':memory:'):
        # Django requires the production database to exist.
        create_empty_production_database()

    if hasattr(request.node.cls, 'db_settings'):
        db_settings = request.node.cls.db_settings
    else:
        db_settings = copy.deepcopy(settings.DATABASES)
        db_settings['default']['NAME'] = DB_NAME

    extra_settings = request.node.get_marker('extra_settings') or ''
    if extra_settings:
        extra_settings = dedent(extra_settings.args[0])
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
        tpkg_path.join(filename).write(dedent(test_code), ensure=True)

    def create_app_file(code, filename):
        test_app_path.join(filename).write(dedent(code), ensure=True)

    testdir.create_test_module = create_test_module
    testdir.create_app_file = create_app_file

    return testdir


@pytest.fixture
def django_testdir_initial(django_testdir):
    """A django_testdir fixture which provides initial_data."""
    django_testdir.makefile('.json', initial_data="""
        [{
            "pk": 1,
            "model": "app.item",
            "fields": { "name": "mark_initial_data" }
        }]""")

    return django_testdir
