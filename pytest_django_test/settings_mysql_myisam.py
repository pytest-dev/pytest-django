from os import environ

from .settings_base import *  # noqa: F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "pytest_django_tests_default",
        "USER": environ.get("TEST_DB_USER", "root"),
        "PASSWORD": environ.get("TEST_DB_PASSWORD", ""),
        "HOST": environ.get("TEST_DB_HOST", "localhost"),
        "OPTIONS": {
            "init_command": "SET default_storage_engine=MyISAM",
            "charset": "utf8mb4",
        },
        "TEST": {
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    },
    "replica": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "pytest_django_tests_replica",
        "USER": environ.get("TEST_DB_USER", "root"),
        "PASSWORD": environ.get("TEST_DB_PASSWORD", ""),
        "HOST": environ.get("TEST_DB_HOST", "localhost"),
        "OPTIONS": {
            "init_command": "SET default_storage_engine=MyISAM",
            "charset": "utf8mb4",
        },
        "TEST": {
            "MIRROR": "default",
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    },
    "second": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "pytest_django_tests_second",
        "USER": environ.get("TEST_DB_USER", "root"),
        "PASSWORD": environ.get("TEST_DB_PASSWORD", ""),
        "HOST": environ.get("TEST_DB_HOST", "localhost"),
        "OPTIONS": {
            "init_command": "SET default_storage_engine=MyISAM",
            "charset": "utf8mb4",
        },
        "TEST": {
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    },
}
