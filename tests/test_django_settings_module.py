import pytest

BARE_SETTINGS = '''
# At least one database must be configured
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    },
}

'''
# This test is a bit meta. :)
DJANGO_SETTINGS_MODULE_TEST = '''
import os

def test_django_settings_module():
    assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.%s'
'''

PYTEST_INI = '''
[pytest]
DJANGO_SETTINGS_MODULE = tpkg.%s
'''

def test_ds_env(testdir, monkeypatch):
    SETTINGS_NAME = 'settings_env'

    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.%s' % SETTINGS_NAME)
    path = testdir.mkpydir('tpkg')
    path.join('%s.py' % SETTINGS_NAME).write(BARE_SETTINGS)
    path.join("test_ds.py").write(DJANGO_SETTINGS_MODULE_TEST % SETTINGS_NAME)

    result = testdir.runpytest('')
    result.stdout.fnmatch_lines([
        "*1 passed*",
    ])

    assert result.ret == 0


def test_ds_ini(testdir, monkeypatch):
    path = testdir.mkpydir('tpkg')

    SETTINGS_NAME = 'settings_ini'

    # Should be ignored
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DO_NOT_USE')


    testdir.tmpdir.join('pytest.ini').write(PYTEST_INI % SETTINGS_NAME)
    path.join('%s.py' % SETTINGS_NAME).write(BARE_SETTINGS)
    path.join("test_ds.py").write(DJANGO_SETTINGS_MODULE_TEST % SETTINGS_NAME)

    result = testdir.runpytest('')
    result.stdout.fnmatch_lines([
        "*1 passed*",
    ])

    assert result.ret == 0



def test_ds_option(testdir, monkeypatch):
    path = testdir.mkpydir('tpkg')

    SETTINGS_NAME = 'settings_option'

    # Should be ignored
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DO_NOT_USE_1')
    testdir.tmpdir.join('pytest.ini').write(PYTEST_INI % 'DO_NOT_USE_2')
    path.join('%s.py' % SETTINGS_NAME).write(BARE_SETTINGS)

    path.join("test_ds.py").write(DJANGO_SETTINGS_MODULE_TEST % SETTINGS_NAME)

    result = testdir.runpytest('--ds=tpkg.%s' % SETTINGS_NAME)
    result.stdout.fnmatch_lines([
        "*1 passed*",
    ])

    assert result.ret == 0


def test_ds_non_existent(testdir, monkeypatch):
    """
    Make sure we do not fail with INTERNALERROR if an incorrect
    DJANGO_SETTINGS_MODULE is given.
    """
    path = testdir.mkpydir('tpkg')

    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DOES_NOT_EXIST')
    path.join("test_foo.py").write('def test_foo(): pass')

    result = testdir.runpytest('')
    result.stderr.fnmatch_lines([
        "ERROR: Could not import settings 'DOES_NOT_EXIST' (Is it on sys.path?): No module named DOES_NOT_EXIST",
    ])
