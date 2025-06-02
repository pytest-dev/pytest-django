import tempfile

from .settings_base import *  # noqa: F403


# This is a SQLite configuration, which uses a file based database for
# tests (via setting TEST_NAME / TEST['NAME']).

# The name as expected / used by Django/pytest_django (tests/db_helpers.py).
_fd, _filename_default = tempfile.mkstemp(prefix="test_")
_fd, _filename_replica = tempfile.mkstemp(prefix="test_")
_fd, _filename_second = tempfile.mkstemp(prefix="test_")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/pytest_django_tests_default",
        "TEST": {
            "NAME": _filename_default,
        },
    },
    "replica": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/pytest_django_tests_replica",
        "TEST": {
            "MIRROR": "default",
            "NAME": _filename_replica,
        },
    },
    "second": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/pytest_django_tests_second",
        "TEST": {
            "NAME": _filename_second,
        },
    },
}
