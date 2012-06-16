
NON_DJANGO_TESTS = '''
import os

from pytest_django.lazy_django import django_is_usable

def test_django_settings_module_not_set():
    """
    Make sure DJANGO_SETTINGS_MODULE really is not defined in this test run.
    """
    assert 'DJANGO_SETTINGS_MODULE' not in os.environ

def test_django_is_usable():
    assert not django_is_usable()

def test_funcarg_client_skip(client):
    assert False, 'This test should be skipped'

'''


def test_non_django_test(testdir, monkeypatch):
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')
    path = testdir.mkpydir('tpkg')
    path.join("test_non_django.py").write(NON_DJANGO_TESTS)

    result = testdir.runpytest('-v')
    result.stdout.fnmatch_lines([
        "*2 passed*",
    ])

    result.stdout.fnmatch_lines([
        "*test_funcarg_client_skip SKIPPED*",
    ])

    assert result.ret == 0
