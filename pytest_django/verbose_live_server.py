import sys
import traceback

from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
from django.test.testcases import LiveServerThread


class VerboseWSGIRequestHandler(WSGIRequestHandler):
    def handle_uncaught_exception(self, request, resolver, exc_info):
        traceback.print_tb(exc_info[2], file=sys.stderr)
        return super(VerboseWSGIRequestHandler, self).handle_uncaught_exception(
            request, resolver, exc_info)


class VerboseLiveServerThread(LiveServerThread):
    def _create_server(self):
        return ThreadedWSGIServer(
            (self.host, self.port),
            VerboseWSGIRequestHandler,
            allow_reuse_address=False
        )
