"""
A Django plugin for pytest that handles creating and destroying the
test environment and test database.

Similar to Django's TestCase, a transaction is started and rolled back for each
test. Additionally, the settings are copied before each test and restored at
the end of the test, so it is safe to modify settings within tests.
"""

import os

from .db_reuse import monkey_patch_creation_for_db_reuse
from .django_compat import (setup_databases, teardown_databases,
                            is_django_unittest, clear_django_outbox,
                            django_setup_item, django_teardown_item)
from .lazy_django import django_settings_is_configured, skip_if_no_django

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


def get_django_settings_module(config):
    """
    Returns the value of DJANGO_SETTINGS_MODULE. The first specified value from
    the following will be used:
     * --ds command line option
     * DJANGO_SETTINGS_MODULE pytest.ini option
     * DJANGO_SETTINGS_MODULE

    """
    ordered_settings = [
        config.option.ds,
        config.getini('DJANGO_SETTINGS_MODULE'),
        os.environ.get('DJANGO_SETTINGS_MODULE')
    ]

    for ds in ordered_settings:
        if ds:
            return ds

    return None


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

    ds = get_django_settings_module(config)

    if ds:
        os.environ['DJANGO_SETTINGS_MODULE'] = ds
    else:
        os.environ.pop('DJANGO_SETTINGS_MODULE', None)

    # Register the marks
    config.addinivalue_line(
        'markers',
        'djangodb(transaction=False, multidb=False): Mark the test as using '
        'the django test database.  The *transaction* argument marks will '
        "allow you to use transactions in the test like Django's "
        'TransactionTestCase while the *multidb* argument will work like '
        "Django's multi_db option on a TestCase: all test databases will be "
        'flushed instead of just the default.')
    config.addinivalue_line(
        'markers',
        'urls(modstr): Use a different URLconf for this test, similar to '
        'the `urls` attribute of Django `TestCase` objects.  *modstr* is '
        'a string specifying the module of a URL config, e.g. '
        '"my_app.test_urls".')


def pytest_sessionstart(session):
    if django_settings_is_configured():
        # This import fiddling is needed to give a proper error message
        # when the Django settings module cannot be found
        try:
            import django
            django  # Silence pyflakes
        except ImportError:
            raise pytest.UsageError('django could not be imported, make sure '
                                    'it is installed and available on your'
                                    'PYTHONPATH')

        from django.conf import settings

        try:
            # Make sure the settings actually gets loaded
            settings.DATABASES
        except ImportError, e:
            # An import error here means that DJANGO_SETTINGS_MODULE could not
            # be imported
            raise pytest.UsageError(*e.args)

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


def validate_urls(marker):
    """This function validates the urls marker

    It checks the signature and creates the `urls` attribute on the
    marker which will have the correct value.
    """
    def apifun(urls):
        return urls
    marker.urls = apifun(*marker.args, **marker.kwargs)


# Trylast is needed to have access to funcargs, live_server suport
# needs this and some funcargs add the djangodb marker which also
# needs this to be called afterwards.
@pytest.mark.trylast
def pytest_runtest_setup(item):
    # Empty the django test outbox
    if django_settings_is_configured():
        clear_django_outbox()

    # Set the URLs if the pytest.urls() decorator has been applied
    marker = getattr(item.obj, 'urls', None)
    if marker:
        skip_if_no_django()
        from django.conf import settings
        from django.core.urlresolvers import clear_url_caches

        validate_urls(marker)
        item.django_urlconf = settings.ROOT_URLCONF
        settings.ROOT_URLCONF = marker.urls
        clear_url_caches()

    if hasattr(item.obj, 'djangodb'):
        # Setup Django databases
        skip_if_no_django()
        validate_djangodb(item.obj.djangodb)
        setup_databases(item.session)
        django_setup_item(item)
    elif django_settings_is_configured() and not is_django_unittest(item):
        # Block access to the Django databases
        import django.db.backends.util

        def cursor_wrapper(*args, **kwargs):
            __tracebackhide__ = True
            __tracebackhide__  # Silence pyflakes
            pytest.fail('Database access not allowed, '
                        'use the "djangodb" mark to enable')

        item.django_cursor_wrapper = django.db.backends.util.CursorWrapper
        django.db.backends.util.CursorWrapper = cursor_wrapper


def pytest_runtest_teardown(item):
    # Call Django code to tear down
    if django_settings_is_configured():
        django_teardown_item(item)

    if hasattr(item, 'django_urlconf'):
        from django.conf import settings
        from django.core.urlresolvers import clear_url_caches
        settings.ROOT_URLCONF = item.django_urlconf
        clear_url_caches()

    if hasattr(item, 'django_cursor_wrapper'):
        import django.db.backends.util
        django.db.backends.util.CursorWrapper = item.django_cursor_wrapper
