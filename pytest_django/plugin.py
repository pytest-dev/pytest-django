"""
A Django plugin for pytest that handles creating and destroying the
test environment and test database.

Similar to Django's TestCase, a transaction is started and rolled back for each
test. Additionally, the settings are copied before each test and restored at
the end of the test, so it is safe to modify settings within tests.
"""

import os

from .db_reuse import monkey_patch_creation_for_db_reuse
from .django_compat import (disable_south_syncdb, setup_databases,
                            teardown_databases, is_django_unittest,
                            clear_django_outbox, django_setup_item,
                            django_teardown_item)
from .lazy_django import django_is_usable, skip_if_no_django

import py
import pytest


def create_django_runner(reuse_db, create_db):
    """Setup the Django test environment

    Return an instance of DjangoTestSuiteRunner which can be used to
    setup and teardown a Django test environment.

    If ``reuse_db`` is True, if found, an existing test database will be used.
    When no test database exists, it will be created.

    If ``create_db`` is True, the test database will be created or re-created,
    no matter what ``reuse_db`` is.
    """

    from django.test.simple import DjangoTestSuiteRunner

    runner = DjangoTestSuiteRunner(interactive=False)
    if reuse_db:
        if not create_db:
            monkey_patch_creation_for_db_reuse()
        runner.teardown_databases = lambda db_config: None
    return runner


def pytest_addoption(parser):
    group = parser.getgroup('django')

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


def pytest_configure(config):
    """Configure DJANGO_SETTINGS_MODULE and register our marks

    The first specified value from the following will be used:

    * --ds command line option
    * DJANGO_SETTINGS_MODULE pytest.ini option
    * DJANGO_SETTINGS_MODULE

    It will set the "ds" config option regardless of the method used
    to set DJANGO_SETTINGS_MODULE, allowing to check for the plugin
    being used by doing `config.getvalue('ds')`.
    """
    ordered_settings = [
        config.option.ds,
        config.getini('DJANGO_SETTINGS_MODULE'),
        os.environ.get('DJANGO_SETTINGS_MODULE')
    ]
    try:
        # Get the first non-empty value
        ds = [x for x in ordered_settings if x][0]
    except IndexError:
        # No value was given -- make sure DJANGO_SETTINGS_MODULE is undefined
        os.environ.pop('DJANGO_SETTINGS_MODULE', None)
    else:
        config.option.ds = ds   # enables config.getvalue('ds')
        os.environ['DJANGO_SETTINGS_MODULE'] = ds

    # Register the marks
    config.addinivalue_line(
        'markers',
        'djangodb(transaction=False, multidb=False): Mark the test as using '
        'the django test database.  The *transaction* argument marks will '
        "allow you to use transactions in the test like Django's "
        'TransactionTestCase while the *multidb* argument will work like '
        "Django's multi_db option on a TestCase: all test databases will be "
        'flushed instead of just the default.')


def pytest_sessionstart(session):
    if django_is_usable():
        from django.conf import settings
        runner = create_django_runner(
            create_db=session.config.getvalue('create_db'),
            reuse_db=session.config.getvalue('reuse_db'))
        runner.setup_test_environment()
        settings.DEBUG_PROPAGATE_EXCEPTIONS = True
        session.django_runner = runner


def pytest_sessionfinish(session, exitstatus):
    runner = getattr(session.config, 'django_runner', None)
    if runner:
        teardown_databases(session)
        runner.teardown_test_environment()


def validate_djangodb(marker):
    """This function validates the djangodb marker

    It checks the signature and creates the `transaction` and
    `mutlidb` attributes on the marker which will have the correct
    value.
    """
    # Use a fake function to check the signature
    def apifun(transaction=False, multidb=False):
        return transaction, multidb
    marker.transaction, marker.multidb = apifun(*marker.args, **marker.kwargs)


# Trylast is needed to have access to funcargs, live_server suport
# needs this and some funcargs add the djangodb marker which also
# needs this to be called afterwards.
@py.test.mark.trylast
def pytest_runtest_setup(item):
    # Validate the djangodb mark early, this makes things easier later
    if hasattr(item.obj, 'djangodb'):
        validate_djangodb(item.obj.djangodb)

    # Empty the django test outbox
    if django_is_usable():
        clear_django_outbox()

    # Set the URLs if the pytest.urls() decorator has been applied
    if hasattr(item.obj, 'urls'):
        skip_if_no_django()
        from django.conf import settings
        from django.core.urlresolvers import clear_url_caches
        item.django_urlconf = settings.ROOT_URLCONF
        settings.ROOT_URLCONF = item.obj.urls
        clear_url_caches()

    # Backwards compatibility
    if hasattr(item.obj, 'transaction_test_case'):
        if not hasattr(item.obj, 'djangodb'):
            item.obj.djangodb = pytest.mark.djangodb(transaction=True)
            validate_djangodb(item.obj.djangodb)
        else:
            item.obj.djangodb.transaction = True

    if hasattr(item.obj, 'djangodb'):
        # Setup Django databases
        skip_if_no_django()
        setup_databases(item.session)
        django_setup_item(item)
    elif django_is_usable() and not is_django_unittest(item):
        # Block access to the Django databases
        import django.db.backends.util

        def cursor_wrapper(*args, **kwargs):
            __tracebackhide__ = True
            pytest.fail('Database access not allowed, '
                        'use the "djangodb" mark to enable')

        item.django_cursor_wrapper = django.db.backends.util.CursorWrapper
        django.db.backends.util.CursorWrapper = cursor_wrapper


def pytest_runtest_teardown(item):
    # Call Django code to tear down
    if django_is_usable():
        django_teardown_item(item)

    if hasattr(item, 'urls'):
        from django.conf import settings
        from django.core.urlresolvers import clear_url_caches
        settings.ROOT_URLCONF = item.django_urlconf
        clear_url_caches()

    if hasattr(item, 'django_cursor_wrapper'):
        import django.db.backends.util
        django.db.backends.util.CursorWrapper = item.django_cursor_wrapper


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
