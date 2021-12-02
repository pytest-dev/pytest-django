"""A pytest plugin which helps testing Django applications

This plugin handles creating and destroying the test environment and
test database and provides some useful text fixtures.
"""

import contextlib
import inspect
import os
import pathlib
import sys
from functools import reduce
from typing import Generator, List, Optional, Tuple, Union

import pytest

from .django_compat import is_django_unittest  # noqa
from .fixtures import _django_db_helper  # noqa
from .fixtures import _live_server_helper  # noqa
from .fixtures import admin_client  # noqa
from .fixtures import admin_user  # noqa
from .fixtures import async_client  # noqa
from .fixtures import async_rf  # noqa
from .fixtures import client  # noqa
from .fixtures import db  # noqa
from .fixtures import django_assert_max_num_queries  # noqa
from .fixtures import django_assert_num_queries  # noqa
from .fixtures import django_capture_on_commit_callbacks  # noqa
from .fixtures import django_db_createdb  # noqa
from .fixtures import django_db_keepdb  # noqa
from .fixtures import django_db_modify_db_settings  # noqa
from .fixtures import django_db_modify_db_settings_parallel_suffix  # noqa
from .fixtures import django_db_modify_db_settings_tox_suffix  # noqa
from .fixtures import django_db_modify_db_settings_xdist_suffix  # noqa
from .fixtures import django_db_reset_sequences  # noqa
from .fixtures import django_db_serialized_rollback  # noqa
from .fixtures import django_db_setup  # noqa
from .fixtures import django_db_use_migrations  # noqa
from .fixtures import django_user_model  # noqa
from .fixtures import django_username_field  # noqa
from .fixtures import live_server  # noqa
from .fixtures import rf  # noqa
from .fixtures import settings  # noqa
from .fixtures import transactional_db  # noqa
from .fixtures import validate_django_db
from .lazy_django import django_settings_is_configured, skip_if_no_django


TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import ContextManager, NoReturn

    import django


SETTINGS_MODULE_ENV = "DJANGO_SETTINGS_MODULE"
CONFIGURATION_ENV = "DJANGO_CONFIGURATION"
INVALID_TEMPLATE_VARS_ENV = "FAIL_INVALID_TEMPLATE_VARS"

_report_header = []


# ############### pytest hooks ################


@pytest.hookimpl()
def pytest_addoption(parser) -> None:
    group = parser.getgroup("django")
    group.addoption(
        "--reuse-db",
        action="store_true",
        dest="reuse_db",
        default=False,
        help="Re-use the testing database if it already exists, "
        "and do not remove it when the test finishes.",
    )
    group.addoption(
        "--create-db",
        action="store_true",
        dest="create_db",
        default=False,
        help="Re-create the database, even if it exists. This "
        "option can be used to override --reuse-db.",
    )
    group.addoption(
        "--ds",
        action="store",
        type=str,
        dest="ds",
        default=None,
        help="Set DJANGO_SETTINGS_MODULE.",
    )
    group.addoption(
        "--dc",
        action="store",
        type=str,
        dest="dc",
        default=None,
        help="Set DJANGO_CONFIGURATION.",
    )
    group.addoption(
        "--nomigrations",
        "--no-migrations",
        action="store_true",
        dest="nomigrations",
        default=False,
        help="Disable Django migrations on test setup",
    )
    group.addoption(
        "--migrations",
        action="store_false",
        dest="nomigrations",
        default=False,
        help="Enable Django migrations on test setup",
    )
    parser.addini(
        CONFIGURATION_ENV, "django-configurations class to use by pytest-django."
    )
    group.addoption(
        "--liveserver",
        default=None,
        help="Address and port for the live_server fixture.",
    )
    parser.addini(
        SETTINGS_MODULE_ENV, "Django settings module to use by pytest-django."
    )

    parser.addini(
        "django_find_project",
        "Automatically find and add a Django project to the " "Python path.",
        type="bool",
        default=True,
    )
    parser.addini(
        "django_debug_mode",
        "How to set the Django DEBUG setting (default `False`). "
        "Use `keep` to not override.",
        default="False",
    )
    group.addoption(
        "--fail-on-template-vars",
        action="store_true",
        dest="itv",
        default=False,
        help="Fail for invalid variables in templates.",
    )
    parser.addini(
        INVALID_TEMPLATE_VARS_ENV,
        "Fail for invalid variables in templates.",
        type="bool",
        default=False,
    )


PROJECT_FOUND = (
    "pytest-django found a Django project in %s "
    "(it contains manage.py) and added it to the Python path.\n"
    'If this is wrong, add "django_find_project = false" to '
    "pytest.ini and explicitly manage your Python path."
)

PROJECT_NOT_FOUND = (
    "pytest-django could not find a Django project "
    "(no manage.py file could be found). You must "
    "explicitly add your Django project to the Python path "
    "to have it picked up."
)

PROJECT_SCAN_DISABLED = (
    "pytest-django did not search for Django "
    "projects since it is disabled in the configuration "
    '("django_find_project = false")'
)


@contextlib.contextmanager
def _handle_import_error(extra_message: str) -> Generator[None, None, None]:
    try:
        yield
    except ImportError as e:
        django_msg = (e.args[0] + "\n\n") if e.args else ""
        msg = django_msg + extra_message
        raise ImportError(msg)


def _add_django_project_to_path(args) -> str:
    def is_django_project(path: pathlib.Path) -> bool:
        try:
            return path.is_dir() and (path / "manage.py").exists()
        except OSError:
            return False

    def arg_to_path(arg: str) -> pathlib.Path:
        # Test classes or functions can be appended to paths separated by ::
        arg = arg.split("::", 1)[0]
        return pathlib.Path(arg)

    def find_django_path(args) -> Optional[pathlib.Path]:
        str_args = (str(arg) for arg in args)
        path_args = [arg_to_path(x) for x in str_args if not x.startswith("-")]

        cwd = pathlib.Path.cwd()
        if not path_args:
            path_args.append(cwd)
        elif cwd not in path_args:
            path_args.append(cwd)

        for arg in path_args:
            if is_django_project(arg):
                return arg
            for parent in arg.parents:
                if is_django_project(parent):
                    return parent
        return None

    project_dir = find_django_path(args)
    if project_dir:
        sys.path.insert(0, str(project_dir.absolute()))
        return PROJECT_FOUND % project_dir
    return PROJECT_NOT_FOUND


def _setup_django() -> None:
    if "django" not in sys.modules:
        return

    import django.conf

    # Avoid force-loading Django when settings are not properly configured.
    if not django.conf.settings.configured:
        return

    import django.apps

    if not django.apps.apps.ready:
        django.setup()

    _blocking_manager.block()


def _get_boolean_value(
    x: Union[None, bool, str],
    name: str,
    default: Optional[bool] = None,
) -> bool:
    if x is None:
        return bool(default)
    if isinstance(x, bool):
        return x
    possible_values = {"true": True, "false": False, "1": True, "0": False}
    try:
        return possible_values[x.lower()]
    except KeyError:
        raise ValueError(
            "{} is not a valid value for {}. "
            "It must be one of {}.".format(x, name, ", ".join(possible_values.keys()))
        )


@pytest.hookimpl()
def pytest_load_initial_conftests(
    early_config,
    parser,
    args: List[str],
) -> None:
    # Register the marks
    early_config.addinivalue_line(
        "markers",
        "django_db(transaction=False, reset_sequences=False, databases=None, "
        "serialized_rollback=False): "
        "Mark the test as using the Django test database.  "
        "The *transaction* argument allows you to use real transactions "
        "in the test like Django's TransactionTestCase.  "
        "The *reset_sequences* argument resets database sequences before "
        "the test.  "
        "The *databases* argument sets which database aliases the test "
        "uses (by default, only 'default'). Use '__all__' for all databases.  "
        "The *serialized_rollback* argument enables rollback emulation for "
        "the test.",
    )
    early_config.addinivalue_line(
        "markers",
        "urls(modstr): Use a different URLconf for this test, similar to "
        "the `urls` attribute of Django's `TestCase` objects.  *modstr* is "
        "a string specifying the module of a URL config, e.g. "
        '"my_app.test_urls".',
    )
    early_config.addinivalue_line(
        "markers",
        "ignore_template_errors(): ignore errors from invalid template "
        "variables (if --fail-on-template-vars is used).",
    )

    options = parser.parse_known_args(args)

    if options.version or options.help:
        return

    django_find_project = _get_boolean_value(
        early_config.getini("django_find_project"), "django_find_project"
    )

    if django_find_project:
        _django_project_scan_outcome = _add_django_project_to_path(args)
    else:
        _django_project_scan_outcome = PROJECT_SCAN_DISABLED

    if (
        options.itv
        or _get_boolean_value(
            os.environ.get(INVALID_TEMPLATE_VARS_ENV), INVALID_TEMPLATE_VARS_ENV
        )
        or early_config.getini(INVALID_TEMPLATE_VARS_ENV)
    ):
        os.environ[INVALID_TEMPLATE_VARS_ENV] = "true"

    def _get_option_with_source(
        option: Optional[str],
        envname: str,
    ) -> Union[Tuple[str, str], Tuple[None, None]]:
        if option:
            return option, "option"
        if envname in os.environ:
            return os.environ[envname], "env"
        cfgval = early_config.getini(envname)
        if cfgval:
            return cfgval, "ini"
        return None, None

    ds, ds_source = _get_option_with_source(options.ds, SETTINGS_MODULE_ENV)
    dc, dc_source = _get_option_with_source(options.dc, CONFIGURATION_ENV)

    if ds:
        _report_header.append("settings: {} (from {})".format(ds, ds_source))
        os.environ[SETTINGS_MODULE_ENV] = ds

        if dc:
            _report_header.append("configuration: {} (from {})".format(dc, dc_source))
            os.environ[CONFIGURATION_ENV] = dc

            # Install the django-configurations importer
            import configurations.importer

            configurations.importer.install()

        # Forcefully load Django settings, throws ImportError or
        # ImproperlyConfigured if settings cannot be loaded.
        from django.conf import settings as dj_settings

        with _handle_import_error(_django_project_scan_outcome):
            dj_settings.DATABASES

    _setup_django()


@pytest.hookimpl()
def pytest_report_header() -> Optional[List[str]]:
    if _report_header:
        return ["django: " + ", ".join(_report_header)]
    return None


@pytest.hookimpl(trylast=True)
def pytest_configure() -> None:
    # Allow Django settings to be configured in a user pytest_configure call,
    # but make sure we call django.setup()
    _setup_django()


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: List[pytest.Item]) -> None:
    # If Django is not configured we don't need to bother
    if not django_settings_is_configured():
        return

    from django.test import TestCase, TransactionTestCase

    def get_order_number(test: pytest.Item) -> int:
        test_cls = getattr(test, "cls", None)
        if test_cls and issubclass(test_cls, TransactionTestCase):
            # Note, TestCase is a subclass of TransactionTestCase.
            uses_db = True
            transactional = not issubclass(test_cls, TestCase)
        else:
            marker_db = test.get_closest_marker("django_db")
            if marker_db:
                (
                    transaction,
                    reset_sequences,
                    databases,
                    serialized_rollback,
                ) = validate_django_db(marker_db)
                uses_db = True
                transactional = transaction or reset_sequences
            else:
                uses_db = False
                transactional = False
            fixtures = getattr(test, "fixturenames", [])
            transactional = transactional or "transactional_db" in fixtures
            uses_db = uses_db or "db" in fixtures

        if transactional:
            return 1
        elif uses_db:
            return 0
        else:
            return 2

    items.sort(key=get_order_number)


@pytest.fixture(autouse=True, scope="session")
def django_test_environment(request) -> None:
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
        from django.test.utils import (
            setup_test_environment, teardown_test_environment,
        )

        debug_ini = request.config.getini("django_debug_mode")
        if debug_ini == "keep":
            debug = None
        else:
            debug = _get_boolean_value(debug_ini, "django_debug_mode", False)

        setup_test_environment(debug=debug)
        request.addfinalizer(teardown_test_environment)


@pytest.fixture(scope="session")
def django_db_blocker() -> "Optional[_DatabaseBlocker]":
    """Wrapper around Django's database access.

    This object can be used to re-enable database access.  This fixture is used
    internally in pytest-django to build the other fixtures and can be used for
    special database handling.

    The object is a context manager and provides the methods
    .unblock()/.block() and .restore() to temporarily enable database access.

    This is an advanced feature that is meant to be used to implement database
    fixtures.
    """
    if not django_settings_is_configured():
        return None

    return _blocking_manager


@pytest.fixture(autouse=True)
def _django_db_marker(request) -> None:
    """Implement the django_db marker, internal to pytest-django."""
    marker = request.node.get_closest_marker("django_db")
    if marker:
        request.getfixturevalue("_django_db_helper")


@pytest.fixture(autouse=True, scope="class")
def _django_setup_unittest(
    request,
    django_db_blocker: "_DatabaseBlocker",
) -> Generator[None, None, None]:
    """Setup a django unittest, internal to pytest-django."""
    if not django_settings_is_configured() or not is_django_unittest(request):
        yield
        return

    # Fix/patch pytest.
    # Before pytest 5.4: https://github.com/pytest-dev/pytest/issues/5991
    # After pytest 5.4: https://github.com/pytest-dev/pytest-django/issues/824
    from _pytest.unittest import TestCaseFunction
    original_runtest = TestCaseFunction.runtest

    def non_debugging_runtest(self) -> None:
        self._testcase(result=self)

    try:
        TestCaseFunction.runtest = non_debugging_runtest  # type: ignore[assignment]

        request.getfixturevalue("django_db_setup")

        with django_db_blocker.unblock():
            yield
    finally:
        TestCaseFunction.runtest = original_runtest  # type: ignore[assignment]


@pytest.fixture(scope="function", autouse=True)
def _dj_autoclear_mailbox() -> None:
    if not django_settings_is_configured():
        return

    from django.core import mail

    del mail.outbox[:]


@pytest.fixture(scope="function")
def mailoutbox(
    django_mail_patch_dns: None,
    _dj_autoclear_mailbox: None,
) -> "Optional[List[django.core.mail.EmailMessage]]":
    if not django_settings_is_configured():
        return None

    from django.core import mail

    return mail.outbox


@pytest.fixture(scope="function")
def django_mail_patch_dns(
    monkeypatch,
    django_mail_dnsname: str,
) -> None:
    from django.core import mail

    monkeypatch.setattr(mail.message, "DNS_NAME", django_mail_dnsname)


@pytest.fixture(scope="function")
def django_mail_dnsname() -> str:
    return "fake-tests.example.com"


@pytest.fixture(autouse=True, scope="function")
def _django_set_urlconf(request) -> None:
    """Apply the @pytest.mark.urls marker, internal to pytest-django."""
    marker = request.node.get_closest_marker("urls")
    if marker:
        skip_if_no_django()
        import django.conf
        from django.urls import clear_url_caches, set_urlconf

        urls = validate_urls(marker)
        original_urlconf = django.conf.settings.ROOT_URLCONF
        django.conf.settings.ROOT_URLCONF = urls
        clear_url_caches()
        set_urlconf(None)

        def restore() -> None:
            django.conf.settings.ROOT_URLCONF = original_urlconf
            # Copy the pattern from
            # https://github.com/django/django/blob/main/django/test/signals.py#L152
            clear_url_caches()
            set_urlconf(None)

        request.addfinalizer(restore)


@pytest.fixture(autouse=True, scope="session")
def _fail_for_invalid_template_variable():
    """Fixture that fails for invalid variables in templates.

    This fixture will fail each test that uses django template rendering
    should a template contain an invalid template variable.
    The fail message will include the name of the invalid variable and
    in most cases the template name.

    It does not raise an exception, but fails, as the stack trace doesn't
    offer any helpful information to debug.
    This behavior can be switched off using the marker:
    ``pytest.mark.ignore_template_errors``
    """

    class InvalidVarException:
        """Custom handler for invalid strings in templates."""

        def __init__(self) -> None:
            self.fail = True

        def __contains__(self, key: str) -> bool:
            return key == "%s"

        @staticmethod
        def _get_origin():
            stack = inspect.stack()

            # Try to use topmost `self.origin` first (Django 1.9+, and with
            # TEMPLATE_DEBUG)..
            for f in stack[2:]:
                func = f[3]
                if func == "render":
                    frame = f[0]
                    try:
                        origin = frame.f_locals["self"].origin
                    except (AttributeError, KeyError):
                        continue
                    if origin is not None:
                        return origin

            from django.template import Template

            # finding the ``render`` needle in the stack
            frameinfo = reduce(
                lambda x, y: y[3] == "render" and "base.py" in y[1] and y or x, stack
            )
            # assert 0, stack
            frame = frameinfo[0]
            # finding only the frame locals in all frame members
            f_locals = reduce(
                lambda x, y: y[0] == "f_locals" and y or x, inspect.getmembers(frame)
            )[1]
            # ``django.template.base.Template``
            template = f_locals["self"]
            if isinstance(template, Template):
                return template.name

        def __mod__(self, var: str) -> str:
            origin = self._get_origin()
            if origin:
                msg = "Undefined template variable '{}' in '{}'".format(var, origin)
            else:
                msg = "Undefined template variable '%s'" % var
            if self.fail:
                pytest.fail(msg)
            else:
                return msg

    if (
        os.environ.get(INVALID_TEMPLATE_VARS_ENV, "false") == "true"
        and django_settings_is_configured()
    ):
        from django.conf import settings as dj_settings

        if dj_settings.TEMPLATES:
            dj_settings.TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = InvalidVarException()


@pytest.fixture(autouse=True)
def _template_string_if_invalid_marker(request) -> None:
    """Apply the @pytest.mark.ignore_template_errors marker,
     internal to pytest-django."""
    marker = request.keywords.get("ignore_template_errors", None)
    if os.environ.get(INVALID_TEMPLATE_VARS_ENV, "false") == "true":
        if marker and django_settings_is_configured():
            from django.conf import settings as dj_settings

            if dj_settings.TEMPLATES:
                dj_settings.TEMPLATES[0]["OPTIONS"]["string_if_invalid"].fail = False


@pytest.fixture(autouse=True, scope="function")
def _django_clear_site_cache() -> None:
    """Clears ``django.contrib.sites.models.SITE_CACHE`` to avoid
    unexpected behavior with cached site objects.
    """

    if django_settings_is_configured():
        from django.conf import settings as dj_settings

        if "django.contrib.sites" in dj_settings.INSTALLED_APPS:
            from django.contrib.sites.models import Site

            Site.objects.clear_cache()


# ############### Helper Functions ################


class _DatabaseBlockerContextManager:
    def __init__(self, db_blocker) -> None:
        self._db_blocker = db_blocker

    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._db_blocker.restore()


class _DatabaseBlocker:
    """Manager for django.db.backends.base.base.BaseDatabaseWrapper.

    This is the object returned by django_db_blocker.
    """

    def __init__(self):
        self._history = []
        self._real_ensure_connection = None

    @property
    def _dj_db_wrapper(self) -> "django.db.backends.base.base.BaseDatabaseWrapper":
        from django.db.backends.base.base import BaseDatabaseWrapper

        # The first time the _dj_db_wrapper is accessed, we will save a
        # reference to the real implementation.
        if self._real_ensure_connection is None:
            self._real_ensure_connection = BaseDatabaseWrapper.ensure_connection

        return BaseDatabaseWrapper

    def _save_active_wrapper(self) -> None:
        self._history.append(self._dj_db_wrapper.ensure_connection)

    def _blocking_wrapper(*args, **kwargs) -> "NoReturn":
        __tracebackhide__ = True
        __tracebackhide__  # Silence pyflakes
        raise RuntimeError(
            "Database access not allowed, "
            'use the "django_db" mark, or the '
            '"db" or "transactional_db" fixtures to enable it.'
        )

    def unblock(self) -> "ContextManager[None]":
        """Enable access to the Django database."""
        self._save_active_wrapper()
        self._dj_db_wrapper.ensure_connection = self._real_ensure_connection
        return _DatabaseBlockerContextManager(self)

    def block(self) -> "ContextManager[None]":
        """Disable access to the Django database."""
        self._save_active_wrapper()
        self._dj_db_wrapper.ensure_connection = self._blocking_wrapper
        return _DatabaseBlockerContextManager(self)

    def restore(self) -> None:
        self._dj_db_wrapper.ensure_connection = self._history.pop()


_blocking_manager = _DatabaseBlocker()


def validate_urls(marker) -> List[str]:
    """Validate the urls marker.

    It checks the signature and creates the `urls` attribute on the
    marker which will have the correct value.
    """

    def apifun(urls: List[str]) -> List[str]:
        return urls

    return apifun(*marker.args, **marker.kwargs)
