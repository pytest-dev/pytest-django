import os
from django.db import connections

try:
    from django.test.testcases import LiveServerThread
    HAS_LIVE_SERVER_SUPPORT = True
except ImportError:
    HAS_LIVE_SERVER_SUPPORT = False


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
