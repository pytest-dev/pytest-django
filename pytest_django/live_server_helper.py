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
