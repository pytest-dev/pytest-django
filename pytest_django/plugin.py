"""
A Django plugin for pytest that handles creating and destroying the
test environment and test database.

Similar to Django's TestCase, a transaction is started and rolled back for each
test. Additionally, the settings are copied before each test and restored at
the end of the test, so it is safe to modify settings within tests.
"""


import sys

from django.conf import settings
from django.core.management import call_command
from django.core import management
from django.core.urlresolvers import clear_url_caches
from django.test.simple import DjangoTestSuiteRunner

from .utils import is_django_unittest, django_setup_item, django_teardown_item

import py

suite_runner = None
old_db_config = None


def _disable_south_management_command():
    management.get_commands()
    # make sure `south` migrations are disabled
    management._commands['syncdb'] = 'django.core'


def pytest_sessionstart(session):
    global suite_runner, old_db_config

    _disable_south_management_command()

    suite_runner = DjangoTestSuiteRunner(interactive=False)

    suite_runner.setup_test_environment()
    old_db_config = suite_runner.setup_databases()

    settings.DATABASE_SUPPORTS_TRANSACTIONS = True


def pytest_sessionfinish(session, exitstatus):
    global suite_runner, old_db_config

    capture = py.io.StdCapture()
    suite_runner.teardown_test_environment()

    suite_runner.teardown_databases(old_db_config)

    unused_out, err = capture.reset()
    sys.stderr.write(err)


_old_urlconf = None


def pytest_runtest_setup(item):
    global _old_urlconf

    # Invoke Django code to prepare the environment for the test run
    if not is_django_unittest(item):
        django_setup_item(item)

    # Set the URLs if the pytest.urls() decorator has been applied
    if hasattr(item.obj, 'urls'):
        _old_urlconf = settings.ROOT_URLCONF
        settings.ROOT_URLCONF = item.obj.urls
        clear_url_caches()


def pytest_runtest_teardown(item):
    global _old_urlconf

    # Call Django code to tear down
    if not is_django_unittest(item):
        django_teardown_item(item)

    if hasattr(item, 'urls') and _old_urlconf is not None:
        settings.ROOT_URLCONF = _old_urlconf
        _old_urlconf = None
        clear_url_caches()


def pytest_namespace():

    def load_fixture(fixture):
        """
        Loads a fixture, useful for loading fixtures in funcargs.

        Example:

            def pytest_funcarg__articles(request):
                pytest.load_fixture('test_articles')
                return Article.objects.all()
        """
        call_command('loaddata', fixture, **{
            'verbosity': 1,
            'commit': not settings.DATABASE_SUPPORTS_TRANSACTIONS
        })

    def urls(urlconf):
        """
        A decorator to change the URLconf for a particular test, similar
        to the `urls` attribute on Django's `TestCase`.

        Example:

            @pytest.urls('myapp.test_urls')
            def test_something(client):
                assert 'Success!' in client.get('/some_path/')
        """
        def wrapper(function):
            function.urls = urlconf
            return function

        return wrapper

    return {'load_fixture': load_fixture, 'urls': urls}
