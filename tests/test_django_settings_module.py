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
    result.stderr.fnmatch_lines(['*ERROR*DOES_NOT_EXIST*'])
