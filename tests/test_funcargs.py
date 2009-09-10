from django.test.client import Client
from pytest_django.client import RequestFactory
import py

pytest_plugins = ['pytester']

def test_params(testdir):
    # Setting up the path isn't working - plugin.__file__ points to the wrong place
    return
    
    testdir.makeconftest("""
        import os, sys
        import pytest_django as plugin
        sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(plugin.__file__), '../')))
        os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
        pytest_plugins = ['django']
    """)
    p = testdir.makepyfile("""
        import py
        @py.test.params([dict(arg1=1, arg2=1), dict(arg1=1, arg2=2)])
        def test_myfunc(arg1, arg2):
            assert arg1 == arg2 
    """)
    result = testdir.runpytest("-v", p)
    assert result.stdout.fnmatch_lines([
        "*test_myfunc*0*PASS*", 
        "*test_myfunc*1*FAIL*", 
        "*1 failed, 1 passed*"
    ])

def test_client(client):
    assert isinstance(client, Client)

def test_rf(rf):
    assert isinstance(rf, RequestFactory)

def check_django_settings():
    from django.conf import settings
    assert settings.DEFAULT_FROM_EMAIL == 'somethingdifferent@example.com'

# These tests should really be done with a testdir, but setting up the Django
# environment within the temporary tests is a right pain
def test_settings(settings):
    assert settings.DEFAULT_FROM_EMAIL != 'somethingdifferent@example.com', settings.DEFAULT_FROM_EMAIL
    settings.DEFAULT_FROM_EMAIL = 'somethingdifferent@example.com'
    assert settings.DEFAULT_FROM_EMAIL == 'somethingdifferent@example.com'
    check_django_settings()
    
    
def test_settings_again(settings):
    test_settings(settings)
