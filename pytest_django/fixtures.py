"""All pytest-django fixtures"""

from __future__ import with_statement

import os
import warnings

import pytest

from . import live_server_helper
from .db_reuse import (monkey_patch_creation_for_db_reuse,
                       monkey_patch_creation_for_db_suffix)
from .django_compat import is_django_unittest
from .lazy_django import get_django_version, skip_if_no_django

__all__ = ['_django_db_setup', 'db', 'transactional_db', 'admin_user',
           'django_user_model', 'django_username_field',
           'client', 'admin_client', 'rf', 'settings', 'live_server',
           '_live_server_helper']


# ############### Internal Fixtures ################

@pytest.fixture(scope='session')
def _django_db_setup(request,
                     _django_test_environment,
                     _django_cursor_wrapper):
    """Session-wide database setup, internal to pytest-django"""
    skip_if_no_django()

    from .compat import setup_databases, teardown_databases

    # xdist
    if hasattr(request.config, 'slaveinput'):
        db_suffix = request.config.slaveinput['slaveid']
    else:
        db_suffix = None

    monkey_patch_creation_for_db_suffix(db_suffix)

    _handle_south()

    if request.config.getvalue('nomigrations'):
        _disable_native_migrations()

    with _django_cursor_wrapper:
        # Monkey patch Django's setup code to support database re-use
        if request.config.getvalue('reuse_db'):
            if not request.config.getvalue('create_db'):
                monkey_patch_creation_for_db_reuse()

        # Create the database
        db_cfg = setup_databases(verbosity=pytest.config.option.verbose,
                                 interactive=False)

    def teardown_database():
        with _django_cursor_wrapper:
            teardown_databases(db_cfg)

    if not request.config.getvalue('reuse_db'):
        request.addfinalizer(teardown_database)


def _django_db_fixture_helper(transactional, request, _django_cursor_wrapper):
    if is_django_unittest(request):
        return

    if not transactional and 'live_server' in request.funcargnames:
        # Do nothing, we get called with transactional=True, too.
        return

    django_case = None

    _django_cursor_wrapper.enable()
    request.addfinalizer(_django_cursor_wrapper.disable)

    if transactional:
        from django import get_version

        if get_version() >= '1.5':
            from django.test import TransactionTestCase as django_case

        else:
            # Django before 1.5 flushed the DB during setUp.
            # Use pytest-django's old behavior with it.
            def flushdb():
                """Flush the database and close database connections"""
                # Django does this by default *before* each test
                # instead of after.
                from django.db import connections
                from django.core.management import call_command

                for db in connections:
                    call_command('flush', interactive=False, database=db,
                                 verbosity=pytest.config.option.verbose)
                for conn in connections.all():
                    conn.close()
            request.addfinalizer(flushdb)

    else:
        from django.test import TestCase as django_case

    if django_case:
        case = django_case(methodName='__init__')
        case._pre_setup()
        request.addfinalizer(case._post_teardown)


def _handle_south():
    from django.conf import settings

    # NOTE: Django 1.7 does not have `management._commands` anymore, which
    # is used by South's `patch_for_test_db_setup` and the code below.
    if 'south' not in settings.INSTALLED_APPS or get_django_version() > (1, 7):
        return

    from django.core import management

    try:
        # if `south` >= 0.7.1 we can use the test helper
        from south.management.commands import patch_for_test_db_setup
    except ImportError:
        # if `south` < 0.7.1 make sure its migrations are disabled
        management.get_commands()
        management._commands['syncdb'] = 'django.core'
    else:
        # Monkey-patch south.hacks.django_1_0.SkipFlushCommand to load
        # initial data.
        # Ref: http://south.aeracode.org/ticket/1395#comment:3
        import south.hacks.django_1_0
        from django.core.management.commands.flush import (
            Command as FlushCommand)

        class SkipFlushCommand(FlushCommand):
            def handle_noargs(self, **options):
                # Reinstall the initial_data fixture.
                from django.core.management import call_command
                # `load_initial_data` got introduces with Django 1.5.
                load_initial_data = options.get('load_initial_data', None)
                if load_initial_data or load_initial_data is None:
                    # Reinstall the initial_data fixture.
                    call_command('loaddata', 'initial_data', **options)
                # no-op to avoid calling flush
                return
        south.hacks.django_1_0.SkipFlushCommand = SkipFlushCommand

        patch_for_test_db_setup()


def _disable_native_migrations():
    from django.conf import settings
    from .migrations import DisableMigrations

    settings.MIGRATION_MODULES = DisableMigrations()


# ############### User visible fixtures ################

@pytest.fixture(scope='function')
def db(request, _django_db_setup, _django_cursor_wrapper):
    """Require a django test database

    This database will be setup with the default fixtures and will have
    the transaction management disabled. At the end of the test the outer
    transaction that wraps the test itself will be rolled back to undo any
    changes to the database (in case the backend supports transactions).
    This is more limited than the ``transactional_db`` resource but
    faster.

    If both this and ``transactional_db`` are requested then the
    database setup will behave as only ``transactional_db`` was
    requested.
    """
    if 'transactional_db' in request.funcargnames \
            or 'live_server' in request.funcargnames:
        return request.getfuncargvalue('transactional_db')
    return _django_db_fixture_helper(False, request, _django_cursor_wrapper)


@pytest.fixture(scope='function')
def transactional_db(request, _django_db_setup, _django_cursor_wrapper):
    """Require a django test database with transaction support

    This will re-initialise the django database for each test and is
    thus slower than the normal ``db`` fixture.

    If you want to use the database with transactions you must request
    this resource.  If both this and ``db`` are requested then the
    database setup will behave as only ``transactional_db`` was
    requested.
    """
    return _django_db_fixture_helper(True, request, _django_cursor_wrapper)


@pytest.fixture()
def client():
    """A Django test client instance."""
    skip_if_no_django()

    from django.test.client import Client

    return Client()


@pytest.fixture()
def django_user_model(db):
    """The class of Django's user model."""
    try:
        from django.contrib.auth import get_user_model
    except ImportError:
        assert get_django_version < (1, 5)
        from django.contrib.auth.models import User as UserModel
    else:
        UserModel = get_user_model()
    return UserModel


@pytest.fixture()
def django_username_field(django_user_model):
    """The fieldname for the username used with Django's user model."""
    try:
        return django_user_model.USERNAME_FIELD
    except AttributeError:
        assert get_django_version < (1, 5)
        return 'username'


@pytest.fixture()
def admin_user(db, django_user_model, django_username_field):
    """A Django admin user.

    This uses an existing user with username "admin", or creates a new one with
    password "password".
    """
    UserModel = django_user_model
    username_field = django_username_field

    try:
        user = UserModel._default_manager.get(**{username_field: 'admin'})
    except UserModel.DoesNotExist:
        extra_fields = {}
        if username_field != 'username':
            extra_fields[username_field] = 'admin'
        user = UserModel._default_manager.create_superuser(
            'admin', 'admin@example.com', 'password', **extra_fields)
    return user


@pytest.fixture()
def admin_client(db, admin_user):
    """A Django test client logged in as an admin user."""
    from django.test.client import Client

    client = Client()
    client.login(username=admin_user.username, password='password')
    return client


@pytest.fixture()
def rf():
    """RequestFactory instance"""
    skip_if_no_django()

    from django.test.client import RequestFactory

    return RequestFactory()


class MonkeyPatchWrapper(object):
    def __init__(self, monkeypatch, wrapped_object):
        super(MonkeyPatchWrapper, self).__setattr__('monkeypatch', monkeypatch)
        super(MonkeyPatchWrapper, self).__setattr__('wrapped_object',
                                                    wrapped_object)

    def __getattr__(self, attr):
        return getattr(self.wrapped_object, attr)

    def __setattr__(self, attr, value):
        self.monkeypatch.setattr(self.wrapped_object, attr, value,
                                 raising=False)

    def __delattr__(self, attr):
        self.monkeypatch.delattr(self.wrapped_object, attr)


@pytest.fixture()
def settings(monkeypatch):
    """A Django settings object which restores changes after the testrun"""
    skip_if_no_django()

    from django.conf import settings as django_settings
    return MonkeyPatchWrapper(monkeypatch, django_settings)


@pytest.fixture(scope='session')
def live_server(request):
    """Run a live Django server in the background during tests

    The address the server is started from is taken from the
    --liveserver command line option or if this is not provided from
    the DJANGO_LIVE_TEST_SERVER_ADDRESS environment variable.  If
    neither is provided ``localhost:8081,8100-8200`` is used.  See the
    Django documentation for it's full syntax.

    NOTE: If the live server needs database access to handle a request
          your test will have to request database access.  Furthermore
          when the tests want to see data added by the live-server (or
          the other way around) transactional database access will be
          needed as data inside a transaction is not shared between
          the live server and test code.

          Static assets will be served for all versions of Django.
          Except for django >= 1.7, if ``django.contrib.staticfiles`` is not
          installed.
    """
    skip_if_no_django()
    addr = request.config.getvalue('liveserver')
    if not addr:
        addr = os.getenv('DJANGO_LIVE_TEST_SERVER_ADDRESS')
    if not addr:
        addr = os.getenv('DJANGO_TEST_LIVE_SERVER_ADDRESS')
        if addr:
            warnings.warn('Please use DJANGO_LIVE_TEST_SERVER_ADDRESS'
                          ' instead of DJANGO_TEST_LIVE_SERVER_ADDRESS.',
                          DeprecationWarning)
    if not addr:
        addr = 'localhost:8081,8100-8200'
    server = live_server_helper.LiveServer(addr)
    request.addfinalizer(server.stop)
    return server


@pytest.fixture(autouse=True, scope='function')
def _live_server_helper(request):
    """Helper to make live_server work, internal to pytest-django.

    This helper will dynamically request the transactional_db fixture
    for a test which uses the live_server fixture.  This allows the
    server and test to access the database without having to mark
    this explicitly which is handy since it is usually required and
    matches the Django behaviour.

    The separate helper is required since live_server can not request
    transactional_db directly since it is session scoped instead of
    function-scoped.
    """
    if 'live_server' in request.funcargnames:
        request.getfuncargvalue('transactional_db')
