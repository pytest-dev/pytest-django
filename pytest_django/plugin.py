"""
A Django plugin for pytest that handles creating and destroying the
test environment and test database.

Similar to Django's TestCase, a transaction is started and rolled back for each
test. Additionally, the settings are copied before each test and restored at
the end of the test, so it is safe to modify settings within tests.
"""

import os

from .db_reuse import monkey_patch_creation_for_db_reuse
from .lazy_django import do_django_imports, django_is_usable
from .utils import is_django_unittest, django_setup_item, django_teardown_item

import py


def get_django_runner(no_db, reuse_db, create_db):
    do_django_imports()

    runner = py.std.django.test.simple.DjangoTestSuiteRunner(interactive=False)

    if no_db:
        def cursor_wrapper_exception(*args, **kwargs):
            raise RuntimeError('No database access is allowed since --no-db '
                               'was used!')

        def setup_databases():
            # Monkey patch CursorWrapper to warn against database usage
            py.std.django.db.backends.util.CursorWrapper = cursor_wrapper_exception

        def teardown_databases(db_config):
            pass

        runner.setup_databases = setup_databases
        runner.teardown_databases = teardown_databases

    elif reuse_db:

        if not create_db:
            monkey_patch_creation_for_db_reuse()

        # Leave the database for the next test run
        runner.teardown_databases = lambda db_config: None

    return runner


def pytest_addoption(parser):
    group = parser.getgroup('django')
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

    group._addoption('--ds',
                     action='store', type='string', dest='ds', default=None,
                     help='Set DJANGO_SETTINGS_MODULE.')

    parser.addini('DJANGO_SETTINGS_MODULE',
                  'Django settings module to use by pytest-django')


def _disable_south_management_command():
    py.std.django.management.management.get_commands()
    py.std.django.management.management._commands['syncdb'] = 'django.core'


def configure_django_settings_module(session):
    # Figure out DJANGO_SETTINGS_MODULE, the first of these that is true:ish
    # will be used
    ordered_settings = [
        session.config.option.ds,
        session.config.getini('DJANGO_SETTINGS_MODULE'),
        os.environ.get('DJANGO_SETTINGS_MODULE')
    ]

    try:
        ds = [x for x in ordered_settings if x][0]
    except IndexError:
        # Make sure it is undefined
        os.environ.pop('DJANGO_SETTINGS_MODULE', None)
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = ds


def pytest_sessionstart(session):
    configure_django_settings_module(session)

    if django_is_usable():
        runner = get_django_runner(no_db=session.config.option.no_db,
                                   create_db=session.config.option.create_db,
                                   reuse_db=session.config.option.reuse_db)

        runner.setup_test_environment()
        old_db_config = runner.setup_databases()

        py.std.django.conf.settings.DEBUG_PROPAGATE_EXCEPTIONS = True

        session.config.pytest_django_runner = runner
        session.config.pytest_django_old_db_config = old_db_config
    else:
        session.config.pytest_django_runner = None


def pytest_sessionfinish(session, exitstatus):
    runner = session.config.pytest_django_runner

    if runner:
        print('\n')
        runner.teardown_databases(session.config.pytest_django_old_db_config)
        runner.teardown_test_environment()


_old_urlconf = None


# trylast is needed to have access to funcargs
@py.test.mark.trylast
def pytest_runtest_setup(item):
    global _old_urlconf

    # Set the URLs if the pytest.urls() decorator has been applied
    if hasattr(item.obj, 'urls'):
        _old_urlconf = py.std.django.conf.settings.ROOT_URLCONF
        py.std.django.conf.settings.ROOT_URLCONF = item.obj.urls
        py.std.django.core.urlresolvers.clear_url_caches()

    # Invoke Django code to prepare the environment for the test run
    if not item.config.option.no_db and not is_django_unittest(item):
        django_setup_item(item)


def pytest_runtest_teardown(item):
    global _old_urlconf

    # Call Django code to tear down
    if not item.config.option.no_db and not is_django_unittest(item):
        django_teardown_item(item)

    if hasattr(item, 'urls') and _old_urlconf is not None:

        py.std.django.conf.settings.ROOT_URLCONF = _old_urlconf
        _old_urlconf = None
        py.std.django.core.urlresolvers.clear_url_caches()


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
