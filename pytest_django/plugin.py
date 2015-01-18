"""A py.test plugin which helps testing Django applications

This plugin handles creating and destroying the test environment and
test database and provides some useful text fixtures.
"""

import os

import contextlib

import pytest
import types

from .django_compat import is_django_unittest
from .fixtures import (_django_db_setup, _live_server_helper, admin_client,
                       admin_user, client, db, django_user_model,
                       django_username_field, live_server, rf, settings,
                       transactional_db)
from .lazy_django import django_settings_is_configured, skip_if_no_django

# Silence linters for imported fixtures.
(_django_db_setup, _live_server_helper, admin_client, admin_user, client, db,
 django_user_model, django_username_field, live_server, rf, settings,
 transactional_db)


SETTINGS_MODULE_ENV = 'DJANGO_SETTINGS_MODULE'
CONFIGURATION_ENV = 'DJANGO_CONFIGURATION'


# ############### pytest hooks ################

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
    group._addoption('--dc',
                     action='store', type='string', dest='dc', default=None,
                     help='Set DJANGO_CONFIGURATION.')
    group._addoption('--nomigrations',
                     action='store_true', dest='nomigrations', default=False,
                     help='Disable Django 1.7 migrations on test setup')
    parser.addini(CONFIGURATION_ENV,
                  'django-configurations class to use by pytest-django.')
    group._addoption('--liveserver', default=None,
                     help='Address and port for the live_server fixture.')
    parser.addini(SETTINGS_MODULE_ENV,
                  'Django settings module to use by pytest-django.')

    parser.addini('django_find_project',
                  'Automatically find and add a Django project to the '
                  'Python path.',
                  default=True)

import py
import sys


def _exists(path, ignore=EnvironmentError):
    try:
        return path.check()
    except ignore:
        return False


PROJECT_FOUND = ('pytest-django found a Django project in %s '
                 '(it contains manage.py) and added it to the Python path.\n'
                 'If this is wrong, add "django_find_project = false" to '
                 'pytest.ini and expliclity manage your Python path.')

PROJECT_NOT_FOUND = ('pytest-django could not find a Django project '
                     '(no manage.py file could be found). You must '
                     'expliclity add your Django project to the Python path '
                     'to have it picked up.')

PROJECT_SCAN_DISABLED = ('pytest-django did not search for Django '
                         'projects since it is disabled in the configuration '
                         '("django_find_project = false")')


@contextlib.contextmanager
def _handle_import_error(extra_message):
    try:
        yield
    except ImportError as e:
        django_msg = (e.args[0] + '\n\n') if e.args else ''
        msg = django_msg + extra_message
        raise ImportError(msg)


def _add_django_project_to_path(args):
    args = [x for x in args if not str(x).startswith("-")]

    if not args:
        args = [py.path.local()]

    for arg in args:
        arg = py.path.local(arg)

        for base in arg.parts(reverse=True):
            manage_py_try = base.join('manage.py')

            if _exists(manage_py_try):
                sys.path.insert(0, str(base))
                return PROJECT_FOUND % base

    return PROJECT_NOT_FOUND


def _setup_django():
    import django

    if hasattr(django, 'setup'):
        django.setup()
    else:
        # Emulate Django 1.7 django.setup() with get_models
        from django.db.models import get_models

        get_models()


def _parse_django_find_project_ini(x):
    if x in (True, False):
        return x

    x = x.lower()
    possible_values = {'true': True,
                       'false': False,
                       '1': True,
                       '0': False}

    try:
        return possible_values[x]
    except KeyError:
        raise ValueError('%s is not a valid value for django_find_project. '
                         'It must be one of %s.'
                         % (x, ', '.join(possible_values.keys())))


def pytest_load_initial_conftests(early_config, parser, args):
    # Register the marks
    early_config.addinivalue_line(
        'markers',
        'django_db(transaction=False): Mark the test as using '
        'the django test database.  The *transaction* argument marks will '
        "allow you to use real transactions in the test like Django's "
        'TransactionTestCase.')
    early_config.addinivalue_line(
        'markers',
        'urls(modstr): Use a different URLconf for this test, similar to '
        'the `urls` attribute of Django `TestCase` objects.  *modstr* is '
        'a string specifying the module of a URL config, e.g. '
        '"my_app.test_urls".')

    options = parser.parse_known_args(args)

    django_find_project = _parse_django_find_project_ini(
        early_config.getini('django_find_project'))

    if django_find_project:
        _django_project_scan_outcome = _add_django_project_to_path(args)
    else:
        _django_project_scan_outcome = PROJECT_SCAN_DISABLED

    # Configure DJANGO_SETTINGS_MODULE
    ds = (options.ds or
          early_config.getini(SETTINGS_MODULE_ENV) or
          os.environ.get(SETTINGS_MODULE_ENV))

    # Configure DJANGO_CONFIGURATION
    dc = (options.dc or
          early_config.getini(CONFIGURATION_ENV) or
          os.environ.get(CONFIGURATION_ENV))

    if ds:
        os.environ[SETTINGS_MODULE_ENV] = ds

        if dc:
            os.environ[CONFIGURATION_ENV] = dc

            # Install the django-configurations importer
            import configurations.importer
            configurations.importer.install()

        # Forcefully load django settings, throws ImportError or
        # ImproperlyConfigured if settings cannot be loaded.
        from django.conf import settings

        with _handle_import_error(_django_project_scan_outcome):
            settings.DATABASES

        _setup_django()


@pytest.mark.trylast
def pytest_configure():
    if django_settings_is_configured():
        _setup_django()


def pytest_runtest_setup(item):

    if django_settings_is_configured() and is_django_unittest(item):
        cls = item.cls

        if hasattr(cls, '__real_setUpClass'):
            return

        cls.__real_setUpClass = cls.setUpClass
        cls.__real_tearDownClass = cls.tearDownClass

        cls.setUpClass = types.MethodType(lambda cls: None, cls)
        cls.tearDownClass = types.MethodType(lambda cls: None, cls)


@pytest.fixture(autouse=True, scope='session')
def _django_test_environment(request):
    """
    Ensure that Django is loaded and has its testing environment setup

    XXX It is a little dodgy that this is an autouse fixture.  Perhaps
        an email fixture should be requested in order to be able to
        use the Django email machinery just like you need to request a
        db fixture for access to the Django database, etc.  But
        without duplicating a lot more of Django's test support code
        we need to follow this model.
    """
    if django_settings_is_configured():
        from django.conf import settings
        from .compat import setup_test_environment, teardown_test_environment
        settings.DEBUG = False
        setup_test_environment()
        request.addfinalizer(teardown_test_environment)


@pytest.fixture(autouse=True, scope='session')
def _django_cursor_wrapper(request):
    """The django cursor wrapper, internal to pytest-django

    This will globally disable all database access. The object
    returned has a .enable() and a .disable() method which can be used
    to temporarily enable database access.
    """
    if not django_settings_is_configured():
        return None

    # util -> utils rename in Django 1.7
    try:
        import django.db.backends.utils
        utils_module = django.db.backends.utils
    except ImportError:
        import django.db.backends.util
        utils_module = django.db.backends.util

    manager = CursorManager(utils_module)
    manager.disable()
    request.addfinalizer(manager.restore)
    return manager


@pytest.fixture(autouse=True)
def _django_db_marker(request):
    """Implement the django_db marker, internal to pytest-django

    This will dynamically request the ``db`` or ``transactional_db``
    fixtures as required by the django_db marker.
    """
    marker = request.keywords.get('django_db', None)
    if marker:
        validate_django_db(marker)
        if marker.transaction:
            request.getfuncargvalue('transactional_db')
        else:
            request.getfuncargvalue('db')


@pytest.fixture(autouse=True, scope='class')
def _django_setup_unittest(request, _django_cursor_wrapper):
    """Setup a django unittest, internal to pytest-django"""
    if django_settings_is_configured() and is_django_unittest(request):
        request.getfuncargvalue('_django_test_environment')
        request.getfuncargvalue('_django_db_setup')

        _django_cursor_wrapper.enable()
        request.node.cls.__real_setUpClass()

        def teardown():
            request.node.cls.__real_tearDownClass()
            _django_cursor_wrapper.restore()

        request.addfinalizer(teardown)


@pytest.fixture(autouse=True, scope='function')
def _django_clear_outbox(request):
    """Clear the django outbox, internal to pytest-django"""
    if django_settings_is_configured():
        from django.core import mail
        mail.outbox = []


@pytest.fixture(autouse=True, scope='function')
def _django_set_urlconf(request):
    """Apply the @pytest.mark.urls marker, internal to pytest-django"""
    marker = request.keywords.get('urls', None)
    if marker:
        skip_if_no_django()
        import django.conf
        from django.core.urlresolvers import clear_url_caches

        validate_urls(marker)
        original_urlconf = django.conf.settings.ROOT_URLCONF
        django.conf.settings.ROOT_URLCONF = marker.urls
        clear_url_caches()

        def restore():
            django.conf.settings.ROOT_URLCONF = original_urlconf

        request.addfinalizer(restore)


# ############### Helper Functions ################


class CursorManager(object):
    """Manager for django.db.backends.util.CursorWrapper

    This is the object returned by _django_cursor_wrapper.

    If created with None as django.db.backends.util the object is a
    no-op.
    """

    def __init__(self, dbutil):
        self._dbutil = dbutil
        self._history = []
        self._real_wrapper = dbutil.CursorWrapper

    def _save_active_wrapper(self):
        return self._history.append(self._dbutil.CursorWrapper)

    def _blocking_wrapper(*args, **kwargs):
        __tracebackhide__ = True
        __tracebackhide__  # Silence pyflakes
        pytest.fail('Database access not allowed, '
                    'use the "django_db" mark to enable')

    def enable(self):
        """Enable access to the django database"""
        self._save_active_wrapper()
        self._dbutil.CursorWrapper = self._real_wrapper

    def disable(self):
        self._save_active_wrapper()
        self._dbutil.CursorWrapper = self._blocking_wrapper

    def restore(self):
        self._dbutil.CursorWrapper = self._history.pop()

    def __enter__(self):
        self.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        self.restore()


def validate_django_db(marker):
    """This function validates the django_db marker

    It checks the signature and creates the `transaction` attribute on
    the marker which will have the correct value.
    """
    def apifun(transaction=False):
        marker.transaction = transaction
    apifun(*marker.args, **marker.kwargs)


def validate_urls(marker):
    """This function validates the urls marker

    It checks the signature and creates the `urls` attribute on the
    marker which will have the correct value.
    """
    def apifun(urls):
        marker.urls = urls
    apifun(*marker.args, **marker.kwargs)
