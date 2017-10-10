"""Tests which check the various ways you can set DJANGO_SETTINGS_MODULE

If these tests fail you probably forgot to install django-configurations.
"""
import pytest

pytest.importorskip('configurations')

try:
    import configurations.importer
    configurations
except ImportError as e:
    if 'LaxOptionParser' in e.args[0]:
        pytest.skip('This version of django-configurations is incompatible with Django: '  # noqa
                    'https://github.com/jezdez/django-configurations/issues/65')  # noqa

BARE_SETTINGS = '''
from configurations import Configuration

class MySettings(Configuration):
    # At least one database must be configured
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        },
    }

    SECRET_KEY = 'foobar'
'''


def test_dc_env(testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.settings_env')
    monkeypatch.setenv('DJANGO_CONFIGURATION', 'MySettings')

    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_env.py')
    settings.write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_settings():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_env'
            assert os.environ['DJANGO_CONFIGURATION'] == 'MySettings'
    """)
    result = testdir.runpytest_subprocess()
    result.stdout.fnmatch_lines(['*1 passed*'])
    assert result.ret == 0


def test_dc_ini(testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.settings_env')
    monkeypatch.setenv('DJANGO_CONFIGURATION', 'MySettings')

    testdir.makeini("""
       [pytest]
       DJANGO_SETTINGS_MODULE = DO_NOT_USE_ini
       DJANGO_CONFIGURATION = DO_NOT_USE_ini
    """)
    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_env.py')
    settings.write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_env'
            assert os.environ['DJANGO_CONFIGURATION'] == 'MySettings'
    """)
    result = testdir.runpytest_subprocess()
    result.stdout.fnmatch_lines(['*1 passed*'])
    assert result.ret == 0


def test_dc_option(testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DO_NOT_USE_env')
    monkeypatch.setenv('DJANGO_CONFIGURATION', 'DO_NOT_USE_env')

    testdir.makeini("""
       [pytest]
       DJANGO_SETTINGS_MODULE = DO_NOT_USE_ini
       DJANGO_CONFIGURATION = DO_NOT_USE_ini
    """)
    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_opt.py')
    settings.write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_opt'
            assert os.environ['DJANGO_CONFIGURATION'] == 'MySettings'
    """)
    result = testdir.runpytest_subprocess('--ds=tpkg.settings_opt', '--dc=MySettings')
    result.stdout.fnmatch_lines(['*1 passed*'])
    assert result.ret == 0
