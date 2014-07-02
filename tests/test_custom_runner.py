BARE_SETTINGS = '''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    },
}
SECRET_KEY = 'foobar'
TEST_RUNNER = 'tpkg.custom_runner.CustomTestRunner'
'''

CUSTOM_RUNNER_IMPL = '''
try:
    from django.test.runner import DiscoverRunner as DjangoTestRunner
except ImportError:
    from django.test.simple import DjangoTestSuiteRunner as DjangoTestRunner


class CustomTestRunner(DjangoTestRunner):
    def __init__(self, **kwargs):
        print('Initializing CustomTestRunner')
        super(CustomTestRunner, self).__init__(**kwargs)
'''


def test_custom_runner(testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'tpkg.settings_custom_runner')
    pkg = testdir.mkpydir('tpkg')
    custom_runner = pkg.join('custom_runner.py')
    custom_runner.write(CUSTOM_RUNNER_IMPL)
    settings = pkg.join('settings_custom_runner.py')
    settings.write(BARE_SETTINGS)

    testdir.makepyfile("""
        def test_dummy():
            assert True
    """)

    result = testdir.runpytest('-sv')
    assert 'Initializing CustomTestRunner' in result.stdout.str()
