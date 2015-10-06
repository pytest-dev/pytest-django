"""A py.test plugin which helps testing Django applications

This plugin handles creating and destroying the test environment and
test database and provides some useful text fixtures.
"""

import contextlib
import inspect
from functools import reduce
import os
import sys
import types

import py
import pytest

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
INVALID_TEMPLATE_VARS_ENV = 'FAIL_INVALID_TEMPLATE_VARS'


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
    group._addoption('--fail-on-template-vars',
                     action='store_true', dest='itv', default=False,
                     help='Fail for invalid variables in templates.')
    parser.addini(INVALID_TEMPLATE_VARS_ENV,
                  'Fail for invalid variables in templates.',
                  default=False)


def _exists(path, ignore=EnvironmentError):
    try:
        return path.check()
    except ignore:
        return False


PROJECT_FOUND = ('pytest-django found a Django project in %s '
                 '(it contains manage.py) and added it to the Python path.\n'
                 'If this is wrong, add "django_find_project = false" to '
                 'pytest.ini and explicitly manage your Python path.')

PROJECT_NOT_FOUND = ('pytest-django could not find a Django project '
                     '(no manage.py file could be found). You must '
                     'explicitly add your Django project to the Python path '
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
    if 'django' not in sys.modules:
        return

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

    if options.version or options.help:
        return

    django_find_project = _parse_django_find_project_ini(
        early_config.getini('django_find_project'))

    if django_find_project:
        _django_project_scan_outcome = _add_django_project_to_path(args)
    else:
        _django_project_scan_outcome = PROJECT_SCAN_DISABLED

    # Configure FAIL_INVALID_TEMPLATE_VARS
    itv = (options.itv or
           os.environ.get(INVALID_TEMPLATE_VARS_ENV) in ['true', 'True', '1'] or
           early_config.getini(INVALID_TEMPLATE_VARS_ENV))

    if itv:
        os.environ[INVALID_TEMPLATE_VARS_ENV] = 'true'

    # Configure DJANGO_SETTINGS_MODULE

    if options.ds:
        ds_source = 'command line option'
        ds = options.ds
    elif SETTINGS_MODULE_ENV in os.environ:
        ds = os.environ[SETTINGS_MODULE_ENV]
        ds_source = 'environment variable'
    elif early_config.getini(SETTINGS_MODULE_ENV):
        ds = early_config.getini(SETTINGS_MODULE_ENV)
        ds_source = 'ini file'
    else:
        ds = None
        ds_source = None

    if ds:
        early_config._dsm_report_header = 'django settings: %s (from %s)' % (ds, ds_source)
    else:
        early_config._dsm_report_header = None

    # Configure DJANGO_CONFIGURATION
    dc = (options.dc or
          os.environ.get(CONFIGURATION_ENV) or
          early_config.getini(CONFIGURATION_ENV))

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


def pytest_report_header(config):
    if config._dsm_report_header:
        return [config._dsm_report_header]


@pytest.mark.trylast
def pytest_configure():
    # Allow Django settings to be configured in a user pytest_configure call,
    # but make sure we call django.setup()
    _setup_django()


def _method_is_defined_at_leaf(cls, method_name):
    super_method = None

    for base_cls in cls.__bases__:
        if hasattr(base_cls, method_name):
            super_method = getattr(base_cls, method_name)

    assert super_method is not None, '%s could not be found in base class' % method_name

    return getattr(cls, method_name).__func__ is not super_method.__func__


_disabled_classmethods = {}


def _disable_class_methods(cls):
    if cls in _disabled_classmethods:
        return

    _disabled_classmethods[cls] = (
        cls.setUpClass,
        _method_is_defined_at_leaf(cls, 'setUpClass'),
        cls.tearDownClass,
        _method_is_defined_at_leaf(cls, 'tearDownClass'),
    )

    cls.setUpClass = types.MethodType(lambda cls: None, cls)
    cls.tearDownClass = types.MethodType(lambda cls: None, cls)


def _restore_class_methods(cls):
    (setUpClass,
     restore_setUpClass,
     tearDownClass,
     restore_tearDownClass) = _disabled_classmethods.pop(cls)

    try:
        del cls.setUpClass
    except AttributeError:
        raise

    try:
        del cls.tearDownClass
    except AttributeError:
        pass

    if restore_setUpClass:
        cls.setUpClass = setUpClass

    if restore_tearDownClass:
        cls.tearDownClass = tearDownClass


def pytest_runtest_setup(item):
    if django_settings_is_configured() and is_django_unittest(item):
        cls = item.cls
        _disable_class_methods(cls)


@pytest.fixture(autouse=True, scope='session')
def _django_test_environment(request):
    """
    Ensure that Django is loaded and has its testing environment setup.

    XXX It is a little dodgy that this is an autouse fixture.  Perhaps
        an email fixture should be requested in order to be able to
        use the Django email machinery just like you need to request a
        db fixture for access to the Django database, etc.  But
        without duplicating a lot more of Django's test support code
        we need to follow this model.
    """
    if django_settings_is_configured():
        _setup_django()
        from django.conf import settings
        from .compat import setup_test_environment, teardown_test_environment
        settings.DEBUG = False
        setup_test_environment()
        request.addfinalizer(teardown_test_environment)


@pytest.fixture(autouse=True, scope='session')
def _django_cursor_wrapper(request):
    """The django cursor wrapper, internal to pytest-django.

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
    """Implement the django_db marker, internal to pytest-django.

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
    """Setup a django unittest, internal to pytest-django."""
    if django_settings_is_configured() and is_django_unittest(request):
        request.getfuncargvalue('_django_test_environment')
        request.getfuncargvalue('_django_db_setup')

        _django_cursor_wrapper.enable()

        cls = request.node.cls

        _restore_class_methods(cls)
        cls.setUpClass()
        _disable_class_methods(cls)

        def teardown():
            _restore_class_methods(cls)
            cls.tearDownClass()
            _django_cursor_wrapper.restore()

        request.addfinalizer(teardown)


@pytest.fixture(autouse=True, scope='function')
def _django_clear_outbox():
    """Clear the django outbox, internal to pytest-django."""
    if django_settings_is_configured():
        from django.core import mail
        mail.outbox = []


@pytest.fixture(autouse=True, scope='function')
def _django_set_urlconf(request):
    """Apply the @pytest.mark.urls marker, internal to pytest-django."""
    marker = request.keywords.get('urls', None)
    if marker:
        skip_if_no_django()
        import django.conf
        from django.core.urlresolvers import clear_url_caches, set_urlconf

        validate_urls(marker)
        original_urlconf = django.conf.settings.ROOT_URLCONF
        django.conf.settings.ROOT_URLCONF = marker.urls
        clear_url_caches()
        set_urlconf(None)

        def restore():
            django.conf.settings.ROOT_URLCONF = original_urlconf
            # Copy the pattern from
            # https://github.com/django/django/blob/master/django/test/signals.py#L152
            clear_url_caches()
            set_urlconf(None)

        request.addfinalizer(restore)


@pytest.fixture(autouse=True, scope='session')
def _fail_for_invalid_template_variable(request):
    """Fixture that fails for invalid variables in templates.

    This fixture will fail each test that uses django template rendering
    should a template contain an invalid template variable.
    The fail message will include the name of the invalid variable and
    in most cases the template name.

    It does not raise an exception, but fails, as the stack trace doesn't
    offer any helpful information to debug.
    This behavior can be switched off using the marker:
    ``ignore_template_errors``
    """
    class InvalidVarException(object):
        """Custom handler for invalid strings in templates."""

        def __init__(self):
            self.fail = True

        def __contains__(self, key):
            """There is a test for '%s' in TEMPLATE_STRING_IF_INVALID."""
            return key == '%s'

        def _get_template(self):
            from django.template import Template

            stack = inspect.stack()
            # finding the ``render`` needle in the stack
            frame = reduce(
                lambda x, y: y[3] == 'render' and 'base.py' in y[1] and y or x,
                stack
            )
            # assert 0, stack
            frame = frame[0]
            # finding only the frame locals in all frame members
            f_locals = reduce(
                lambda x, y: y[0] == 'f_locals' and y or x,
                inspect.getmembers(frame)
            )[1]
            # ``django.template.base.Template``
            template = f_locals['self']
            if isinstance(template, Template):
                return template

        def __mod__(self, var):
            """Handle TEMPLATE_STRING_IF_INVALID % var."""
            template = self._get_template()
            if template:
                msg = "Undefined template variable '%s' in '%s'" % (var, template.name)
            else:
                msg = "Undefined template variable '%s'" % var
            if self.fail:
                pytest.fail(msg, pytrace=False)
            else:
                return msg
    if os.environ.get(INVALID_TEMPLATE_VARS_ENV, 'false') == 'true':
        if django_settings_is_configured():
            import django
            from django.conf import settings

            if django.VERSION >= (1, 8) and settings.TEMPLATES:
                settings.TEMPLATES[0]['OPTIONS']['string_if_invalid'] = InvalidVarException()
            else:
                settings.TEMPLATE_STRING_IF_INVALID = InvalidVarException()


@pytest.fixture(autouse=True)
def _template_string_if_invalid_marker(request):
    """Apply the @pytest.mark.ignore_template_errors marker,
     internal to pytest-django."""
    marker = request.keywords.get('ignore_template_errors', None)
    if os.environ.get(INVALID_TEMPLATE_VARS_ENV, 'false') == 'true':
        if marker and django_settings_is_configured():
            import django
            from django.conf import settings

            if django.VERSION >= (1, 8) and settings.TEMPLATES:
                settings.TEMPLATES[0]['OPTIONS']['string_if_invalid'].fail = False
            else:
                settings.TEMPLATE_STRING_IF_INVALID.fail = False

# ############### Helper Functions ################


class CursorManager(object):
    """Manager for django.db.backends.util.CursorWrapper.

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
                    'use the "django_db" mark to enable it.')

    def enable(self):
        """Enable access to the Django database."""
        self._save_active_wrapper()
        self._dbutil.CursorWrapper = self._real_wrapper

    def disable(self):
        """Disable access to the Django database."""
        self._save_active_wrapper()
        self._dbutil.CursorWrapper = self._blocking_wrapper

    def restore(self):
        self._dbutil.CursorWrapper = self._history.pop()

    def __enter__(self):
        self.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        self.restore()


def validate_django_db(marker):
    """Validate the django_db marker.

    It checks the signature and creates the `transaction` attribute on
    the marker which will have the correct value.
    """
    def apifun(transaction=False):
        marker.transaction = transaction
    apifun(*marker.args, **marker.kwargs)


def validate_urls(marker):
    """Validate the urls marker.

    It checks the signature and creates the `urls` attribute on the
    marker which will have the correct value.
    """
    def apifun(urls):
        marker.urls = urls
    apifun(*marker.args, **marker.kwargs)
