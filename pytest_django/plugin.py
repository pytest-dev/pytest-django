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

import django.db.backends.util


from .utils import is_django_unittest, django_setup_item, django_teardown_item
from .db_reuse import monkey_patch_creation_for_db_reuse

import py


suite_runner = None
old_db_config = None


def get_runner(config):
    runner = DjangoTestSuiteRunner(interactive=False)

    if config.option.no_db:
        def cursor_wrapper_exception(*args, **kwargs):
            raise RuntimeError('No database access is allowed since --no-db was used!')

        def setup_databases():
            # Monkey patch CursorWrapper to warn against database usage
            django.db.backends.util.CursorWrapper = cursor_wrapper_exception

        def teardown_databases(db_config):
            pass

        runner.setup_databases = setup_databases
        runner.teardown_databases = teardown_databases

    elif config.option.reuse_db:

        if not config.option.create_db:
            monkey_patch_creation_for_db_reuse()

        # Leave the database for the next test run
        runner.teardown_databases = lambda db_config: None

    return runner


def pytest_addoption(parser):
    group = parser.getgroup('django database setup')
    group._addoption('--no-db',
                     action='store_true', dest='no_db', default=False,
                     help='Run tests without setting up database access. Any '
                          'communication with databases will result in an '
                          'exception.')

    group._addoption('--reuse-db',
                     action='store_true', dest='reuse_db', default=False,
                     help='Re-use the testing database if it already exists, '
                          'and do not remove it when the test finishes. This '
                          'option will be ignored when --no-db is given.')

    group._addoption('--create-db',
                     action='store_true', dest='create_db', default=False,
                     help='Re-create the database, even if it exists. This '
                          'option will be ignored if not --reuse-db is given.')


def _disable_south_management_command():
    management.get_commands()
    # make sure `south` migrations are disabled
    management._commands['syncdb'] = 'django.core'


def pytest_sessionstart(session):
    global suite_runner, old_db_config

    _disable_south_management_command()

    suite_runner = get_runner(session.config)
    suite_runner.setup_test_environment()

    old_db_config = suite_runner.setup_databases()

    settings.DEBUG_PROPAGATE_EXCEPTIONS = True


def pytest_sessionfinish(session, exitstatus):
    global suite_runner, old_db_config

    capture = py.io.StdCapture()
    suite_runner.teardown_test_environment()

    suite_runner.teardown_databases(old_db_config)

    unused_out, err = capture.reset()
    sys.stderr.write(err)


_old_urlconf = None


# trylast is needed to have access to funcargs
@py.test.mark.trylast
def pytest_runtest_setup(item):
    global _old_urlconf

    # Set the URLs if the pytest.urls() decorator has been applied
    if hasattr(item.obj, 'urls'):
        _old_urlconf = settings.ROOT_URLCONF
        settings.ROOT_URLCONF = item.obj.urls
        clear_url_caches()

    # Invoke Django code to prepare the environment for the test run
    if not item.config.option.no_db and not is_django_unittest(item):
        django_setup_item(item)


def pytest_runtest_teardown(item):
    global _old_urlconf

    # Call Django code to tear down
    if not item.config.option.no_db and not is_django_unittest(item):
        django_teardown_item(item)

    if hasattr(item, 'urls') and _old_urlconf is not None:
        settings.ROOT_URLCONF = _old_urlconf
        _old_urlconf = None
        clear_url_caches()


def pytest_namespace():
    def load_fixture(fixture):
        raise Exception('load_fixture is deprecated. Use a standard Django '
                        'test case or invoke call_command("loaddata", fixture)'
                        'instead.')

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
