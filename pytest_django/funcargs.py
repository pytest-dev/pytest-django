import copy
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db import connections
from django.test.client import RequestFactory, Client
from django.test.testcases import LiveServerThread

from .marks import transaction_test_case


def pytest_funcarg__client(request):
    """
    Returns a Django test client instance.
    """
    return Client()


def pytest_funcarg__admin_client(request):
    """
    Returns a Django test client logged in as an admin user.
    """

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


def pytest_funcarg__rf(request):
    """
    Returns a RequestFactory instance.
    """
    return RequestFactory()


def pytest_funcarg__settings(request):
    """
    Returns a Django settings object that restores any changes after the test
    has been run.
    """
    old_settings = copy.deepcopy(settings)

    def restore_settings():
        for setting in dir(old_settings):
            if setting == setting.upper():
                setattr(settings, setting, getattr(old_settings, setting))
    request.addfinalizer(restore_settings)
    return settings


class LiveServer(object):
    def __init__(self, host, possible_ports):

        connections_override = {}

        for conn in connections.all():
            # If using in-memory sqlite databases, pass the connections to
            # the server thread.
            if (conn.settings_dict['ENGINE'] == 'django.db.backends.sqlite3'
                and conn.settings_dict['NAME'] == ':memory:'):
                # Explicitly enable thread-shareability for this connection
                conn.allow_thread_sharing = True
                connections_override[conn.alias] = conn

        self.thread = LiveServerThread(host, possible_ports, connections_override)
        self.thread.daemon = True
        self.thread.start()

        self.thread.is_ready.wait()

        if self.thread.error:
            raise self.thread.error

    def __unicode__(self):
        return 'http://%s:%s' % (self.thread.host, self.thread.port)

    def __repr__(self):
        return '<LiveServer listenting at %s>' % unicode(self)

    def __add__(self, other):
        # Support string concatenation
        return unicode(self) + other


def get_live_server_host_ports():
    # This code is copy-pasted from django/test/testcases.py

    specified_address = os.environ.get('DJANGO_LIVE_TEST_SERVER_ADDRESS', 'localhost:8081')

    # The specified ports may be of the form '8000-8010,8080,9200-9300'
    # i.e. a comma-separated list of ports or ranges of ports, so we break
    # it down into a detailed list of all possible ports.
    possible_ports = []
    try:
        host, port_ranges = specified_address.split(':')
        for port_range in port_ranges.split(','):
            # A port range can be of either form: '8000' or '8000-8010'.
            extremes = map(int, port_range.split('-'))
            assert len(extremes) in [1, 2]
            if len(extremes) == 1:
                # Port range of the form '8000'
                possible_ports.append(extremes[0])
            else:
                # Port range of the form '8000-8010'
                for port in range(extremes[0], extremes[1] + 1):
                    possible_ports.append(port)
    except Exception:
        raise Exception('Invalid address ("%s") for live server.' % specified_address)

    return (host, possible_ports)


def pytest_funcarg__live_server(request):
    def setup_live_server():
        return LiveServer(*get_live_server_host_ports())

    def teardown_live_server(live_server):
        live_server.thread.join()

    return request.cached_setup(setup=setup_live_server, teardown=teardown_live_server, scope='session')
