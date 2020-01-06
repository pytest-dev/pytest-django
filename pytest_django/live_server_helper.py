import six


@six.python_2_unicode_compatible
class LiveServer(object):
    """The liveserver fixture

    This is the object that the ``live_server`` fixture returns.
    The ``live_server`` fixture handles creation and stopping.
    """

    def __init__(self, addr):
        from django.test.testcases import LiveServerTestCase
        from django.conf import settings

        if "django.contrib.staticfiles" in settings.INSTALLED_APPS:
            from django.contrib.staticfiles.handlers import StaticFilesHandler
        else:
            from django.test.testcases import _StaticFilesHandler as StaticFilesHandler

        class CustomLiveServerTestCase(LiveServerTestCase):
            static_handler = StaticFilesHandler

        self._dj_testcase = CustomLiveServerTestCase("__init__")
        self._dj_testcase.setUpClass()

    def stop(self):
        if not hasattr(self._dj_testcase._live_server_modified_settings, "wrapped"):
            self._dj_testcase._live_server_modified_settings.enable()
        self._dj_testcase.tearDownClass()

    @property
    def url(self):
        return self._dj_testcase.live_server_url

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
