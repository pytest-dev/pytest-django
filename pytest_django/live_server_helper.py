from typing import Any, Dict


class LiveServer:
    """The liveserver fixture

    This is the object that the ``live_server`` fixture returns.
    The ``live_server`` fixture handles creation and stopping.
    """

    def __init__(self, addr: str) -> None:
        from django.db import connections
        from django.test.testcases import LiveServerThread
        from django.test.utils import modify_settings

        liveserver_kwargs = {}  # type: Dict[str, Any]

        connections_override = {}
        for conn in connections.all():
            # If using in-memory sqlite databases, pass the connections to
            # the server thread.
            if (
                conn.settings_dict["ENGINE"] == "django.db.backends.sqlite3"
                and conn.settings_dict["NAME"] == ":memory:"
            ):
                # Explicitly enable thread-shareability for this connection
                conn.allow_thread_sharing = True
                connections_override[conn.alias] = conn

        liveserver_kwargs["connections_override"] = connections_override
        from django.conf import settings

        if "django.contrib.staticfiles" in settings.INSTALLED_APPS:
            from django.contrib.staticfiles.handlers import StaticFilesHandler

            liveserver_kwargs["static_handler"] = StaticFilesHandler
        else:
            from django.test.testcases import _StaticFilesHandler

            liveserver_kwargs["static_handler"] = _StaticFilesHandler

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

    def stop(self) -> None:
        """Stop the server"""
        self.thread.terminate()
        self.thread.join()

    @property
    def url(self) -> str:
        return "http://{}:{}".format(self.thread.host, self.thread.port)

    def __str__(self) -> str:
        return self.url

    def __add__(self, other) -> str:
        return "{}{}".format(self, other)

    def __repr__(self) -> str:
        return "<LiveServer listening at %s>" % self.url
