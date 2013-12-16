import pytest
import py

import shutil
import copy


pytest_plugins = 'pytester'

TESTS_DIR = py.path.local(__file__)


from django.conf import settings


from .db_helpers import (create_empty_production_database, get_db_engine,
                         DB_NAME)


@pytest.fixture(scope='function')
def django_testdir(testdir, monkeypatch):
    if get_db_engine() in ('mysql', 'postgresql_psycopg2'):
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
SECRET_KEY = 'foobar'
''' % {'db_settings': repr(db_settings)}

    tpkg_path = testdir.mkpydir('tpkg')
    app_source = TESTS_DIR.dirpath('app')

    # Copy the test app to make it available in the new test run
    shutil.copytree(py.builtin._totext(app_source),
                    py.builtin._totext(tpkg_path.join('app')))
    tpkg_path.join("db_test_settings.py").write(test_settings)

    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.db_test_settings')

    def create_test_module(test_code, filename='test_the_test.py'):
        tpkg_path = testdir.tmpdir / 'tpkg'
        tpkg_path.join(filename).write(test_code)

    def create_conftest(testdir, conftest_code):
        return create_test_module(testdir, conftest_code, 'conftest.py')

    testdir.create_test_module = create_test_module
    testdir.create_conftest = create_conftest

    return testdir




