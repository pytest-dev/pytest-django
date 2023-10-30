from .settings_base import *  # noqa: F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    "replica": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "MIRROR": "default",
        },
    },
    "second": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}
