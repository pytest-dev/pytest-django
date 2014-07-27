"""All pytest-django fixtures"""

from __future__ import with_statement

import os

import pytest

from . import live_server_helper
from .db_reuse import (monkey_patch_creation_for_db_reuse,
                       monkey_patch_creation_for_db_suffix)
from .django_compat import is_django_unittest
from .lazy_django import get_django_version, skip_if_no_django

__all__ = ['_django_db_setup', 'db', 'transactional_db',
           'client', 'admin_client', 'rf', 'settings', 'live_server',
           '_live_server_helper']


################ Internal Fixtures ################


@pytest.fixture(scope='session')
def _django_db_setup(request,
                     _django_test_environment,
                     _django_cursor_wrapper):
    """Session-wide database setup, internal to pytest-django"""
    skip_if_no_django()

    from .compat import setup_databases, teardown_databases
    from django.core import management

    # xdist
    if hasattr(request.config, 'slaveinput'):
        db_suffix = request.config.slaveinput['slaveid']
    else:
        db_suffix = None

    monkey_patch_creation_for_db_suffix(db_suffix)

    # Disable south's syncdb command
    commands = management.get_commands()
    if commands['syncdb'] == 'south':
        management._commands['syncdb'] = 'django.core'

    with _django_cursor_wrapper:
        # Monkey patch Django's setup code to support database re-use
        if request.config.getvalue('reuse_db'):
            if not request.config.getvalue('create_db'):
                monkey_patch_creation_for_db_reuse()

        # Create the database
        db_cfg = setup_databases(verbosity=0, interactive=False)

    def teardown_database():
        with _django_cursor_wrapper:
            teardown_databases(db_cfg)

    if not request.config.getvalue('reuse_db'):
        request.addfinalizer(teardown_database)

def _django_db_fixture_helper(transactional, request, _django_cursor_wrapper):
    if is_django_unittest(request.node):
        return

    if transactional:
        _django_cursor_wrapper.enable()

        def flushdb():
            """Flush the database and close database connections"""
            # Django does this by default *before* each test
            # instead of after.
            from django.db import connections
            from django.core.management import call_command

            for db in connections:
                call_command('flush', verbosity=0,
                             interactive=False, database=db)
            for conn in connections.all():
                conn.close()

        request.addfinalizer(_django_cursor_wrapper.disable)
        request.addfinalizer(flushdb)
    else:
        if 'live_server' in request.funcargnames:
            return
        from django.test import TestCase

        _django_cursor_wrapper.enable()
        _django_cursor_wrapper._is_transactional = False
        case = TestCase(methodName='__init__')
        case._pre_setup()
        request.addfinalizer(_django_cursor_wrapper.disable)
        request.addfinalizer(case._post_teardown)

################ User visible fixtures ################


@pytest.fixture(scope='function')
def db(request, _django_db_setup, _django_cursor_wrapper):
    """Require a django test database

    This database will be setup with the default fixtures and will
    have the transaction management disabled.  At the end of the test
    the transaction will be rolled back to undo any changes to the
    database.  This is more limited than the ``transactional_db``
    resource but faster.

    If both this and ``transactional_db`` are requested then the
    database setup will behave as only ``transactional_db`` was
    requested.
    """
    if 'transactional_db' in request.funcargnames:
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
    """A Django test client instance"""
    skip_if_no_django()

    from django.test.client import Client

    return Client()


@pytest.fixture()
def admin_client(db):
    """
    A Django test client logged in as an admin user

    """
    has_custom_user_model_support = get_django_version() >= (1, 5)

    # When using Django >= 1.5 the username field is variable, so
    # get 'username field' by using UserModel.USERNAME_FIELD
    if has_custom_user_model_support:
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        username_field = UserModel.USERNAME_FIELD
    else:
        from django.contrib.auth.models import User as UserModel
        username_field = 'username'

    from django.test.client import Client

    try:
        UserModel._default_manager.get(**{username_field: 'admin'})
    except UserModel.DoesNotExist:
        extra_fields = {}
        if username_field != 'username':
            extra_fields[username_field] = 'admin'
        UserModel._default_manager.create_superuser('admin', 'admin@example.com',
                                                    'password', **extra_fields)

    client = Client()
    client.login(username='admin', password='password')
    return client


@pytest.fixture()
def rf():
    """RequestFactory instance"""
    skip_if_no_django()

    from django.test.client import RequestFactory

    return RequestFactory()


class MonkeyPatchWrapper(object):
    def __init__(self, monkeypatch, wrapped_object):
        from django.test.utils import override_settings

        wrapper = override_settings()
        wrapper.enable()
        super(MonkeyPatchWrapper, self).__setattr__('wrapper', wrapper)
        super(MonkeyPatchWrapper, self).__setattr__('_default_settings',
                                                    wrapper.wrapped)
        super(MonkeyPatchWrapper, self).__setattr__('monkeypatch', monkeypatch)
        super(MonkeyPatchWrapper, self).__setattr__('wrapped_object',
                                                    wrapped_object)

    def __getattr__(self, attr):
        return getattr(self.wrapped_object, attr)

    def __setattr__(self, attr, value):
        self.wrapper.options[attr] = value
        self.wrapper.enable()

    def __delattr__(self, attr):
        self.wrapper.options[attr] = None
        self.wrapper.enable()
        self.monkeypatch.delattr(self.wrapped_object, attr)

    def disable(self):
        self.wrapper.wrapped = self._default_settings
        self.wrapper.disable()


@pytest.fixture()
def settings(request, monkeypatch):
    """A Django settings object which restores changes after the testrun"""
    skip_if_no_django()

    from django.conf import settings as django_settings
    fixture = MonkeyPatchWrapper(monkeypatch, django_settings)
    request.addfinalizer(fixture.disable)
    return fixture


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
    """
    skip_if_no_django()
    addr = request.config.getvalue('liveserver')
    if not addr:
        addr = os.getenv('DJANGO_TEST_LIVE_SERVER_ADDRESS')
    if not addr:
        addr = 'localhost:8081,8100-8200'
    server = live_server_helper.LiveServer(addr)
    request.addfinalizer(server.stop)
    return server


@pytest.fixture(autouse=True, scope='function')
def _live_server_helper(request):
    """Helper to make live_server work, internal to pytest-django

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
