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
    """ Dummy custom test runner implementation """
    def setup_databases(self, **kwargs):
        return super(CustomTestRunner, self).setup_databases(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        return super(CustomTestRunner, self).teardown(old_config, **kwargs)
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
    result.stdout.fnmatch_lines(
        ["<class 'tpkg.custom_runner.CustomTestRunner'>"])
