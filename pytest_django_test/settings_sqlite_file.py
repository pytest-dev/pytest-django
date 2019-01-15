import tempfile

from pytest_django_test.settings_base import *  # noqa

# This is a SQLite configuration, which uses a file based database for
# tests (via setting TEST_NAME / TEST['NAME']).

# The name as expected / used by Django/pytest_django (tests/db_helpers.py).
_fd, _filename = tempfile.mkstemp(prefix="test_")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/should_never_be_accessed",
        "TEST": {"NAME": _filename},
    }
}
