"""Tests which check the various ways you can set DJANGO_SETTINGS_MODULE

If these tests fail you probably forgot to install django-configurations.
"""
import pytest


def setup_module(mod):
    pytest.importorskip('cbs')


BARE_SETTINGS = '''
from cbs import BaseSettings

class MySettings(BaseSettings):
    PROJECT_NAME = 'tpkg'
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
    monkeypatch.setenv('DJANGO_SETTINGS_CLASS', 'MySettings')

    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_env.py')
    settings.write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_settings():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_env'
            assert os.environ['DJANGO_SETTINGS_CLASS'] == 'MySettings'
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*1 passed*'])
    assert result.ret == 0


def test_dc_ini(testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.settings_env')
    monkeypatch.setenv('DJANGO_SETTINGS_CLASS', 'MySettings')

    testdir.makeini("""
       [pytest]
       DJANGO_SETTINGS_MODULE = DO_NOT_USE_ini
       DJANGO_SETTINGS_CLASS = DO_NOT_USE_ini
    """)
    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_env.py')
    settings.write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_env'
            assert os.environ['DJANGO_SETTINGS_CLASS'] == 'MySettings'
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*1 passed*'])
    assert result.ret == 0


def test_dc_option(testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DO_NOT_USE_env')
    monkeypatch.setenv('DJANGO_SETTINGS_CLASS', 'DO_NOT_USE_env')

    testdir.makeini("""
       [pytest]
       DJANGO_SETTINGS_MODULE = DO_NOT_USE_ini
       DJANGO_SETTINGS_CLASS = DO_NOT_USE_ini
    """)
    pkg = testdir.mkpydir('tpkg')
    settings = pkg.join('settings_opt.py')
    settings.write(BARE_SETTINGS)
    testdir.makepyfile("""
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_opt'
            assert os.environ['DJANGO_SETTINGS_CLASS'] == 'MySettings'
    """)
    result = testdir.runpytest('--ds=tpkg.settings_opt', '--dcbs=MySettings')
    result.stdout.fnmatch_lines(['*1 passed*'])
    assert result.ret == 0
