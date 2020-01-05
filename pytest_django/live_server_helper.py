import django
import six


@six.python_2_unicode_compatible
class LiveServer(object):
    """The liveserver fixture

    This is the object that the ``live_server`` fixture returns.
    The ``live_server`` fixture handles creation and stopping.
    """

    def __init__(self, addr):
        from django.db import connections
        from django.test.testcases import LiveServerThread
        from django.test.utils import modify_settings

        self.orig_conns = {}
        connections_override = {}
        for conn in connections.all():
            # If using in-memory sqlite databases, pass the connections to
            # the server thread.
            if conn.settings_dict["ENGINE"] == "django.db.backends.sqlite3":
                test_dbname = conn.settings_dict['TEST']['NAME'] or ':memory:'
                if test_dbname == ":memory:":
                    connections_override[conn.alias] = conn
                    # Explicitly enable thread-shareability for this connection
                    if django.VERSION >= (2, 2):
                        conn.inc_thread_sharing()
                        self.orig_conns[conn] = True
                    else:
                        self.orig_conns[conn] = conn.allow_thread_sharing
                        conn.allow_thread_sharing = True

        liveserver_kwargs = {"connections_override": connections_override}
        from django.conf import settings

        if "django.contrib.staticfiles" in settings.INSTALLED_APPS:
            from django.contrib.staticfiles.handlers import StaticFilesHandler

            liveserver_kwargs["static_handler"] = StaticFilesHandler
        else:
            from django.test.testcases import _StaticFilesHandler

            liveserver_kwargs["static_handler"] = _StaticFilesHandler

        if django.VERSION < (1, 11):
            host, possible_ports = parse_addr(addr)
            self.thread = LiveServerThread(host, possible_ports, **liveserver_kwargs)
        else:
            try:
                host, port = addr.split(":")
            except ValueError:
                host = addr
            else:
                liveserver_kwargs["port"] = int(port)
            self.thread = LiveServerThread(host, **liveserver_kwargs)

        self._live_server_modified_settings = modify_settings(
            ALLOWED_HOSTS={"append": host}
        )

        self.thread.daemon = True
        self.thread.start()
        self.thread.is_ready.wait()

        if self.thread.error:
            raise self.thread.error

    def stop(self):
        """Stop the server"""
        self.thread.terminate()
        self.thread.join()

        if django.VERSION >= (2, 2):
            for conn in self.orig_conns:
                conn.inc_thread_sharing()
        else:
            for conn, val in self.orig_conns.items():
                conn.allow_thread_sharing = val
        self.orig_conns = {}

    @property
    def url(self):
        return "http://%s:%s" % (self.thread.host, self.thread.port)

    def __str__(self):
        return self.url

    def __add__(self, other):
        return "%s%s" % (self, other)

    def __repr__(self):
        return "<LiveServer listening at %s>" % self.url


def parse_addr(specified_address):
    """Parse the --liveserver argument into a host/IP address and port range"""
    # This code is based on
    # django.test.testcases.LiveServerTestCase.setUpClass

    # The specified ports may be of the form '8000-8010,8080,9200-9300'
    # i.e. a comma-separated list of ports or ranges of ports, so we break
    # it down into a detailed list of all possible ports.
    possible_ports = []
    try:
        host, port_ranges = specified_address.split(":")
        for port_range in port_ranges.split(","):
            # A port range can be of either form: '8000' or '8000-8010'.
            extremes = list(map(int, port_range.split("-")))
            assert len(extremes) in (1, 2)
            if len(extremes) == 1:
                # Port range of the form '8000'
                possible_ports.append(extremes[0])
            else:
                # Port range of the form '8000-8010'
                for port in range(extremes[0], extremes[1] + 1):
                    possible_ports.append(port)
    except Exception:
        raise Exception('Invalid address ("%s") for live server.' % specified_address)

    return host, possible_ports
