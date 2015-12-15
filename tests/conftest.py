import copy
import shutil
from textwrap import dedent

import py
import pytest
from django.conf import settings

from pytest_django_test.db_helpers import (create_empty_production_database,
                                           DB_NAME, get_db_engine)

pytest_plugins = 'pytester'

REPOSITORY_ROOT = py.path.local(__file__).join('..')


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'django_project: options for the django_testdir fixture')


def _marker_apifun(extra_settings='',
                   create_manage_py=False,
                   project_root=None):
    return {
        'extra_settings': extra_settings,
        'create_manage_py': create_manage_py,
        'project_root': project_root,
    }


@pytest.fixture
def testdir(testdir):
    # pytest 2.7.x compatibility
    if not hasattr(testdir, 'runpytest_subprocess'):
        testdir.runpytest_subprocess = testdir.runpytest

    return testdir


@pytest.fixture(scope='function')
def django_testdir(request, testdir, monkeypatch):
    marker = request.node.get_marker('django_project')

    options = _marker_apifun(**(marker.kwargs if marker else {}))

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
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'tpkg.app',
        ]
        SECRET_KEY = 'foobar'

        MIDDLEWARE_CLASSES = (
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        )

        TEMPLATES = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {},
            },
        ]

        %(extra_settings)s
    ''') % {
        'db_settings': repr(db_settings),
        'extra_settings': dedent(options['extra_settings'])}

    if options['project_root']:
        project_root = testdir.mkdir(options['project_root'])
    else:
        project_root = testdir.tmpdir

    tpkg_path = project_root.mkdir('tpkg')

    if options['create_manage_py']:
        project_root.ensure('manage.py')

    tpkg_path.ensure('__init__.py')

    app_source = REPOSITORY_ROOT.dirpath('pytest_django_test/app')
    test_app_path = tpkg_path.join('app')

    # Copy the test app to make it available in the new test run
    shutil.copytree(py.builtin._totext(app_source),
                    py.builtin._totext(test_app_path))
    tpkg_path.join("the_settings.py").write(test_settings)

    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.the_settings')

    def create_test_module(test_code, filename='test_the_test.py'):
        r = tpkg_path.join(filename)
        r.write(dedent(test_code), ensure=True)
        return r

    def create_app_file(code, filename):
        r = test_app_path.join(filename)
        r.write(dedent(code), ensure=True)
        return r

    testdir.create_test_module = create_test_module
    testdir.create_app_file = create_app_file
    testdir.project_root = project_root

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

    def _create_initial_south_migration():
        """
        Create initial South migration for pytest_django_test/app/models.py.
        """
        django_testdir.mkpydir('tpkg/app/south_migrations')
        django_testdir.create_app_file("""
            from south.v2 import SchemaMigration
            from south.db import db

            class Migration(SchemaMigration):
                def forwards(self, orm):
                    db.create_table(u'app_item', (
                        (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                        (u'name', self.gf('django.db.models.fields.CharField')(max_length=100)),
                    ))
                    db.send_create_signal(u'app', ['Item'])
                    print("mark_south_migration_forwards")
                    db.create_table(u'app_itemmetadata', (
                        (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                        (u'owner', self.gf('django.db.models.fields.related.ForeignKey')(orm['app.Item'])),
                    ))
                    db.send_create_signal(u'app', ['ItemMetadata'])
                    print("mark_south_migration_forwards"),


                def backwards(self, orm):
                    db.delete_table(u'app_item')
                    db.delete_table(u'app_itemmetadata')

                models = {
                    u'app.item': {
                        'Meta': {'object_name': 'Item'},
                        u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                        u'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
                    },
                    u'app.itemmetadata': {
                        'Meta': {'object_name': 'ItemMetadata'},
                        u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                        u'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['app.Item']"})
                    }
                }

                complete_apps = ['app']
            """, 'south_migrations/0001_initial.py')
    django_testdir.create_initial_south_migration = _create_initial_south_migration

    return django_testdir
