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

CONFTEST_AGAINST_DOUBLE_DJANGO_SETUP = '''
def pytest_configure():
    # we have to prevent bug where pytest calls django.setup() multiple
    # times, breaking the logging conf (and pytest-capturelog plugin)
    import django.apps
    if django.apps.apps.ready:
        django.setup = lambda: UNEXISTING_VAR
'''

    
def test_django_setup_uniqueness(testdir, monkeypatch):
    """
    The django.setup() function shall not be called multiple times by pytest-django, 
    since it resets logging conf each time.
    """
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')
    #testdir.makeini("""
    #   [pytest]
    #   DJANGO_SETTINGS_MODULE = tpkg.settings_ini
    #""")
    pkg = testdir.mkpydir('tpkg')
    pkg.join('settings_ini.py').write(BARE_SETTINGS)
    pkg.join('conftest.py').write(CONFTEST_AGAINST_DOUBLE_DJANGO_SETUP)
    testdir.makepyfile("""
        import os

        def test_ds():
            assert True
    """)
    result = testdir.runpytest_subprocess('--ds=tpkg.settings_ini')
    result.stdout.fnmatch_lines(['*1 passed*'])
    assert result.ret == 0
    

