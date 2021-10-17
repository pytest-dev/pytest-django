from .settings_base import *  # noqa: F401 F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/should_not_be_accessed",
    },
    "replica": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/should_not_be_accessed",
        "TEST": {
            "MIRROR": "default",
        },
    },
    "second": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/should_not_be_accessed",
    },
}
