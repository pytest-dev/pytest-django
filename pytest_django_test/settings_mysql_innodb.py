from os import environ

from .settings_base import *  # noqa: F401 F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "pytest_django_should_never_get_accessed",
        "USER": environ.get("TEST_DB_USER", "root"),
        "PASSWORD": environ.get("TEST_DB_PASSWORD", ""),
        "HOST": environ.get("TEST_DB_HOST", "localhost"),
        "OPTIONS": {
            "init_command": "SET default_storage_engine=InnoDB",
            "charset": "utf8mb4",
        },
        "TEST": {
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    },
}
