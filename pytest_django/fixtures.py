"""All pytest-django fixtures"""

from __future__ import with_statement

import os

import pytest

from . import live_server_helper
from .db_reuse import monkey_patch_creation_for_db_reuse
from .django_compat import is_django_unittest
from .lazy_django import skip_if_no_django

__all__ = ['_django_db_setup', 'db', 'transactional_db',
           'client', 'admin_client', 'rf', 'settings', 'live_server',
           '_live_server_helper']


################ Internal Fixtures ################


@pytest.fixture(scope='session')
def _django_db_setup(request, _django_runner, _django_cursor_wrapper):
    """Session-wide database setup, internal to pytest-django"""
    skip_if_no_django()

    from django.core import management

    # Disable south's syncdb command
    commands = management.get_commands()
    if commands['syncdb'] == 'south':
        management._commands['syncdb'] = 'django.core'

    with _django_cursor_wrapper:

        # Monkey patch Django's setup code to support database re-use
        if request.config.getvalue('reuse_db'):
            if not request.config.getvalue('create_db'):
                monkey_patch_creation_for_db_reuse()
            _django_runner.teardown_databases = lambda db_cfg: None

        # Create the database
        db_cfg = _django_runner.setup_databases()

    def teardown_database():
        with _django_cursor_wrapper:
            _django_runner.teardown_databases(db_cfg)

    request.addfinalizer(teardown_database)


################ User visible fixtures ################


@pytest.fixture(scope='function')
def db(request, _django_db_setup, _django_cursor_wrapper):
    """Require a django test database

    This database will be setup with the default fixtures and will
    have the transaction management disabled.  At the end of the test
    the transaction will be rolled back to undo any changes to the
    database.  This is more limited then the ``transaction_db``
    resource but faster.

    If both this and ``transaction_db`` are requested then the
    database setup will behave as only ``transaction_db`` was
    requested.
    """
    if ('transactional_db' not in request.funcargnames and
            'live_server' not in request.funcargnames and
            not is_django_unittest(request.node)):

        from django.test import TestCase

        _django_cursor_wrapper.enable()
        case = TestCase(methodName='__init__')
        case._pre_setup()
        request.addfinalizer(case._post_teardown)
        request.addfinalizer(_django_cursor_wrapper.disable)


@pytest.fixture(scope='function')
def transactional_db(request, _django_db_setup, _django_cursor_wrapper):
    """Require a django test database with transaction support

    This will re-initialise the django database for each test and is
    thus slower then the normal ``db`` fixture.

    If you want to use the database with transactions you must request
    this resource.  If both this and ``db`` are requested then the
    database setup will behave as only ``transaction_db`` was
    requested.
    """
    if not is_django_unittest(request.node):
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


@pytest.fixture()
def client():
    """A Django test client instance"""
    skip_if_no_django()

    from django.test.client import Client

    return Client()


@pytest.fixture()
def admin_client(db):
    """A Django test client logged in as an admin user"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
    except ImportError:
        from django.contrib.auth.models import User
    from django.test.client import Client

    try:
        User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_user('admin', 'admin@example.com',
                                        'password')
        user.is_staff = True
        user.is_superuser = True
        user.save()

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
def settings(request, monkeypatch):
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
    for a tests which uses the live_server fixture.  This allows the
    server and test to access the database without having to mark
    this explicitly which is handy since it is usually required and
    matches the Django behaviour.

    The separate helper is required since live_server can not request
    transactional_db directly since it is session scoped instead of
    function-scoped.
    """
    if 'live_server' in request.funcargnames:
        request.getfuncargvalue('transactional_db')
