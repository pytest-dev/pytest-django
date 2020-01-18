import tempfile

from .settings_base import *  # noqa: F401 F403

# This is a SQLite configuration, which uses a file based database for
# tests (via setting TEST_NAME / TEST['NAME']).

# The name as expected / used by Django/pytest_django (tests/db_helpers.py).
_fd, _filename = tempfile.mkstemp(prefix="test_")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/pytest_django_should_never_get_accessed",
        "TEST": {"NAME": _filename},
    }
}
