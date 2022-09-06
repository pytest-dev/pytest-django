import sys
import traceback

from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
from django.test.testcases import LiveServerThread


class VerboseWSGIRequestHandler(WSGIRequestHandler):
    debug_on_traceback = False

    def handle_uncaught_exception(self, request, resolver, exc_info):
        traceback.print_tb(exc_info[2], file=sys.stderr)
        if self.debug_on_traceback:
            import pytest
            pytest.set_trace()

        return super(VerboseWSGIRequestHandler, self).handle_uncaught_exception(
            request, resolver, exc_info)


class VerboseDebuggingWSGIRequestHandler(VerboseWSGIRequestHandler):
    debug_on_traceback = True


class VerboseLiveServerThread(LiveServerThread):
    request_handler_class = VerboseWSGIRequestHandler

    def _create_server(self):
        return ThreadedWSGIServer(
            (self.host, self.port),
            self.request_handler_class,
            allow_reuse_address=False
        )


class VerboseDebuggingLiveServerThread(VerboseLiveServerThread):
    request_handler_class = VerboseDebuggingWSGIRequestHandler
