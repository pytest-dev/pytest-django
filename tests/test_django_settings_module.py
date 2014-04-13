"""Tests which check the various ways you can set DJANGO_SETTINGS_MODULE

If these tests fail you probably forgot to run "python setup.py develop".
"""

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
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*1 passed*'])


def test_ds_ini(testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DO_NOT_USE')
    testdir.makeini("""\
       [pytest]
       DJANGO_SETTINGS_MODULE = tpkg.settings_ini
    """)
    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_ini.py')
    settings.write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_ini'
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*1 passed*'])


def test_ds_option(testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DO_NOT_USE_env')
    testdir.makeini("""\
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
    result = testdir.runpytest('--ds=tpkg.settings_opt')
    result.stdout.fnmatch_lines(['*1 passed*'])


def test_ds_non_existent(testdir, monkeypatch):
    # Make sure we do not fail with INTERNALERROR if an incorrect
    # DJANGO_SETTINGS_MODULE is given.
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DOES_NOT_EXIST')
    testdir.makepyfile('def test_ds(): pass')
    result = testdir.runpytest()
    result.stderr.fnmatch_lines(
        ["*Could not import settings 'DOES_NOT_EXIST' (Is it on sys.path?*):*"])


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
    r = testdir.runpytest()
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
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*1 passed*'])


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
    r = testdir.runpytest()
    assert r.ret == 0
