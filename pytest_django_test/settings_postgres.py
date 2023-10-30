from os import environ

from .settings_base import *  # noqa: F403


# PyPy compatibility
try:
    from psycopg2cffi import compat

    compat.register()
except ImportError:
    pass


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pytest_django_tests_default",
        "USER": environ.get("TEST_DB_USER", ""),
        "PASSWORD": environ.get("TEST_DB_PASSWORD", ""),
        "HOST": environ.get("TEST_DB_HOST", ""),
    },
    "replica": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pytest_django_tests_replica",
        "USER": environ.get("TEST_DB_USER", ""),
        "PASSWORD": environ.get("TEST_DB_PASSWORD", ""),
        "HOST": environ.get("TEST_DB_HOST", ""),
        "TEST": {
            "MIRROR": "default",
        },
    },
    "second": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pytest_django_tests_second",
        "USER": environ.get("TEST_DB_USER", ""),
        "PASSWORD": environ.get("TEST_DB_PASSWORD", ""),
        "HOST": environ.get("TEST_DB_HOST", ""),
    },
}
