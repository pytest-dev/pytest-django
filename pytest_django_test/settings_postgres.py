from os import environ

from .settings_base import *  # noqa: F401 F403

# PyPy compatibility
try:
    from psycopg2cffi import compat

    compat.register()
except ImportError:
    pass


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pytest_django_should_never_get_accessed",
        "USER": environ.get("TEST_DB_USER", ""),
        "PASSWORD": environ.get("TEST_DB_PASSWORD", ""),
        "HOST": environ.get("TEST_DB_HOST", ""),
    },
}
