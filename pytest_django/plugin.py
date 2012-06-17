"""
A Django plugin for pytest that handles creating and destroying the
test environment and test database.

Similar to Django's TestCase, a transaction is started and rolled back for each
test. Additionally, the settings are copied before each test and restored at
the end of the test, so it is safe to modify settings within tests.
"""

import os

from .db_reuse import monkey_patch_creation_for_db_reuse
from .django_compat import (disable_south_syncdb, is_django_unittest,
                            django_setup_item, django_teardown_item)
from .lazy_django import django_is_usable, skip_if_no_django

import py


def get_django_test_runner(no_db, reuse_db, create_db):
    """
    Returns an instance of DjangoTestSuiteRunner that can be used to setup
    a Django test environment.

    If ``no_db`` is True, no test databases will be created at all. If any
    database access takes place, an exception will be raised.

    If ``reuse_db`` is True, if found, an existing test database will be used.
    When no test database exists, it will be created.

    If ``create_db`` is True, the test database will be created or re-created,
    no matter what ``reuse_db`` is.
    """

    from django.test.simple import DjangoTestSuiteRunner

    runner = DjangoTestSuiteRunner(interactive=False)

    if no_db:
        def cursor_wrapper_exception(*args, **kwargs):
            raise RuntimeError('No database access is allowed since --no-db '
                               'was used!')

        def setup_databases():
            import django.db.backends.utils
            # Monkey patch CursorWrapper to warn against database usage
            django.db.backends.util.CursorWrapper = cursor_wrapper_exception

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


def configure_django_settings_module(session):
    """
    Configures DJANGO_SETTINGS_MODULE. The first specified value from the
    following will be used:
     * --ds command line option
     * DJANGO_SETTINGS_MODULE pytest.ini option
     * DJANGO_SETTINGS_MODULE

    """
    ordered_settings = [
        session.config.option.ds,
        session.config.getini('DJANGO_SETTINGS_MODULE'),
        os.environ.get('DJANGO_SETTINGS_MODULE')
    ]

    try:
        # Get the first non-empty value
        ds = [x for x in ordered_settings if x][0]
    except IndexError:
        # No value was given -- make sure DJANGO_SETTINGS_MODULE is undefined
        os.environ.pop('DJANGO_SETTINGS_MODULE', None)
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = ds


def pytest_sessionstart(session):
    configure_django_settings_module(session)

    if django_is_usable():
        from django.conf import settings

        runner = get_django_test_runner(no_db=session.config.option.no_db,
                                        create_db=session.config.option.create_db,
                                        reuse_db=session.config.option.reuse_db)

        disable_south_syncdb()
        runner.setup_test_environment()
        old_db_config = runner.setup_databases()

        settings.DEBUG_PROPAGATE_EXCEPTIONS = True

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


# trylast is needed to have access to funcargs
@py.test.mark.trylast
def pytest_runtest_setup(item):
    # Set the URLs if the pytest.urls() decorator has been applied
    if hasattr(item.obj, 'urls'):
        skip_if_no_django()

        from django.conf import settings
        from django.core.urlresolvers import clear_url_caches

        item.config.old_urlconf = settings.ROOT_URLCONF
        settings.ROOT_URLCONF = item.obj.urls
        clear_url_caches()

    # Invoke Django code to prepare the environment for the test run
    if not item.config.option.no_db and not is_django_unittest(item):
        django_setup_item(item)


def pytest_runtest_teardown(item):
    # Call Django code to tear down
    if not item.config.option.no_db and not is_django_unittest(item):
        django_teardown_item(item)

    if hasattr(item, 'urls'):
        from django.conf import settings
        from django.core.urlresolvers import clear_url_caches

        settings.ROOT_URLCONF = item.config.old_urlconf
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
