"""Tests which check the various ways you can set DJANGO_SETTINGS_MODULE

If these tests fail you probably forgot to run "python setup.py develop".
"""

import django
import pytest


BARE_SETTINGS = '''
# At least one database must be configured
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    },
}
SECRET_KEY = 'foobar'
'''


def test_ds_ini(testdir, monkeypatch):
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')
    testdir.makeini("""
       [pytest]
       DJANGO_SETTINGS_MODULE = tpkg.settings_ini
    """)
    pkg = testdir.mkpydir('tpkg')
    pkg.join('settings_ini.py').write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_ini'
    """)
    result = testdir.runpytest_subprocess()
    assert result.parseoutcomes()['passed'] == 1
    result.stdout.fnmatch_lines(['Django settings: tpkg.settings_ini '
                                 '(from ini file)*'])
    assert result.ret == 0


def test_ds_env(testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.settings_env')
    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_env.py')
    settings.write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_settings():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_env'
    """)
    result = testdir.runpytest_subprocess()
    result.stdout.fnmatch_lines(['Django settings: tpkg.settings_env (from '
                                 'environment variable)*'])
    assert result.parseoutcomes()['passed'] == 1


def test_ds_option(testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DO_NOT_USE_env')
    testdir.makeini("""
       [pytest]
       DJANGO_SETTINGS_MODULE = DO_NOT_USE_ini
    """)
    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_opt.py')
    settings.write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_opt'
    """)
    result = testdir.runpytest_subprocess('--ds=tpkg.settings_opt')
    result.stdout.fnmatch_lines(['Django settings: tpkg.settings_opt '
                                 '(from command line option)'])
    assert result.parseoutcomes()['passed'] == 1


def test_ds_env_override_ini(testdir, monkeypatch):
    "DSM env should override ini."
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.settings_env')
    testdir.makeini("""\
       [pytest]
       DJANGO_SETTINGS_MODULE = DO_NOT_USE_ini
    """)
    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_env.py')
    settings.write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_env'
    """)
    result = testdir.runpytest_subprocess()
    assert result.parseoutcomes()['passed'] == 1
    assert result.ret == 0


def test_ds_non_existent(testdir, monkeypatch):
    """
    Make sure we do not fail with INTERNALERROR if an incorrect
    DJANGO_SETTINGS_MODULE is given.
    """
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DOES_NOT_EXIST')
    testdir.makepyfile('def test_ds(): pass')
    result = testdir.runpytest_subprocess()
    result.stderr.fnmatch_lines(["*ImportError:*DOES_NOT_EXIST*"])
    assert result.ret != 0


def test_ds_after_user_conftest(testdir, monkeypatch):
    """
    Test that the settings module can be imported, after pytest has adjusted
    the sys.path.
    """
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'settings_after_conftest')
    testdir.makepyfile('def test_ds(): pass')
    testdir.makepyfile(settings_after_conftest="SECRET_KEY='secret'")
    # testdir.makeconftest("import sys; print(sys.path)")
    result = testdir.runpytest_subprocess('-v')
    result.stdout.fnmatch_lines(['*1 passed*'])
    assert result.ret == 0


def test_ds_in_pytest_configure(testdir, monkeypatch):
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')
    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_ds.py')
    settings.write(BARE_SETTINGS)
    testdir.makeconftest("""
        import os

        from django.conf import settings

        def pytest_configure():
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                                      'tpkg.settings_ds')
    """)

    testdir.makepyfile("""
        def test_anything():
            pass
    """)

    r = testdir.runpytest_subprocess()
    assert r.parseoutcomes()['passed'] == 1
    assert r.ret == 0


def test_django_settings_configure(testdir, monkeypatch):
    """
    Make sure Django can be configured without setting
    DJANGO_SETTINGS_MODULE altogether, relying on calling
    django.conf.settings.configure() and then invoking pytest.
    """
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')

    p = testdir.makepyfile(run="""
            from django.conf import settings
            settings.configure(SECRET_KEY='set from settings.configure()',
                               DATABASES={'default': {
                                   'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'
                               }},
                               INSTALLED_APPS=['django.contrib.auth',
                                               'django.contrib.contenttypes',])

            import pytest

            pytest.main()
    """)

    testdir.makepyfile("""
        import pytest

        from django.conf import settings
        from django.test.client import RequestFactory
        from django.test import TestCase
        from django.contrib.auth.models import User

        def test_access_to_setting():
            assert settings.SECRET_KEY == 'set from settings.configure()'

        # This test requires Django to be properly configured to be run
        def test_rf(rf):
            assert isinstance(rf, RequestFactory)

        # This tests that pytest-django actually configures the database
        # according to the settings above
        class ATestCase(TestCase):
            def test_user_count(self):
                assert User.objects.count() == 0

        @pytest.mark.django_db
        def test_user_count():
            assert User.objects.count() == 0

    """)
    result = testdir.runpython(p)
    result.stdout.fnmatch_lines([
        "*4 passed*",
    ])


def test_settings_in_hook(testdir, monkeypatch):
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')
    testdir.makeconftest("""
        from django.conf import settings

        def pytest_configure():
            settings.configure(SECRET_KEY='set from pytest_configure',
                               DATABASES={'default': {
                                   'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
                               INSTALLED_APPS=['django.contrib.auth',
                                               'django.contrib.contenttypes',])
    """)
    testdir.makepyfile("""
        import pytest
        from django.conf import settings
        from django.contrib.auth.models import User

        def test_access_to_setting():
            assert settings.SECRET_KEY == 'set from pytest_configure'

        @pytest.mark.django_db
        def test_user_count():
            assert User.objects.count() == 0
    """)
    r = testdir.runpytest_subprocess()
    assert r.ret == 0


def test_django_not_loaded_without_settings(testdir, monkeypatch):
    """
    Make sure Django is not imported at all if no Django settings is specified.
    """
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')
    testdir.makepyfile("""
        import sys
        def test_settings():
            assert 'django' not in sys.modules
    """)
    result = testdir.runpytest_subprocess()
    result.stdout.fnmatch_lines(['*1 passed*'])
    assert result.ret == 0


def test_debug_false(testdir, monkeypatch):
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')
    testdir.makeconftest("""
        from django.conf import settings

        def pytest_configure():
            settings.configure(SECRET_KEY='set from pytest_configure',
                               DEBUG=True,
                               DATABASES={'default': {
                                   'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
                               INSTALLED_APPS=['django.contrib.auth',
                                               'django.contrib.contenttypes',])
    """)

    testdir.makepyfile("""
        from django.conf import settings
        def test_debug_is_false():
            assert settings.DEBUG is False
    """)

    r = testdir.runpytest_subprocess()
    assert r.ret == 0


@pytest.mark.skipif(not hasattr(django, 'setup'),
                    reason="This Django version does not support app loading")
@pytest.mark.django_project(extra_settings="""
    INSTALLED_APPS = [
        'tpkg.app.apps.TestApp',
    ]
""")
def test_django_setup_sequence(django_testdir):
    django_testdir.create_app_file("""
        from django.apps import apps, AppConfig


        class TestApp(AppConfig):
            name = 'tpkg.app'

            def ready(self):
                try:
                    populating = apps.loading
                except AttributeError:  # Django < 2.0
                    populating = apps._lock.locked()
                print('READY(): populating=%r' % populating)
        """, 'apps.py')

    django_testdir.create_app_file("""
        from django.apps import apps

        try:
            populating = apps.loading
        except AttributeError:  # Django < 2.0
            populating = apps._lock.locked()

        print('IMPORT: populating=%r,ready=%r' % (populating, apps.ready))
        SOME_THING = 1234
        """, 'models.py')

    django_testdir.create_app_file("", '__init__.py')
    django_testdir.makepyfile("""
        from django.apps import apps
        from tpkg.app.models import SOME_THING

        def test_anything():
            try:
                populating = apps.loading
            except AttributeError:  # Django < 2.0
                populating = apps._lock.locked()

            print('TEST: populating=%r,ready=%r' % (populating, apps.ready))
        """)

    result = django_testdir.runpytest_subprocess('-s', '--tb=line')
    result.stdout.fnmatch_lines(['*IMPORT: populating=True,ready=False*'])
    result.stdout.fnmatch_lines(['*READY(): populating=True*'])
    if django.VERSION < (2, 0):
        result.stdout.fnmatch_lines(['*TEST: populating=False,ready=True*'])
    else:
        result.stdout.fnmatch_lines(['*TEST: populating=True,ready=True*'])
    assert result.ret == 0


def test_no_ds_but_django_imported(testdir, monkeypatch):
    """pytest-django should not bail out, if "django" has been imported
    somewhere, e.g. via pytest-splinter."""

    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')

    testdir.makepyfile("""
        import os
        import django

        from pytest_django.lazy_django import django_settings_is_configured

        def test_django_settings_is_configured():
            assert django_settings_is_configured() is False

        def test_env():
            assert 'DJANGO_SETTINGS_MODULE' not in os.environ

        def test_cfg(pytestconfig):
            assert pytestconfig.option.ds is None
    """)
    r = testdir.runpytest_subprocess('-s')
    assert r.ret == 0


def test_no_django_settings_but_django_imported(testdir, monkeypatch):
    """Make sure we do not crash when Django happens to be imported, but
    settings is not properly configured"""
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')
    testdir.makeconftest('import django')
    r = testdir.runpytest_subprocess('--help')
    assert r.ret == 0
