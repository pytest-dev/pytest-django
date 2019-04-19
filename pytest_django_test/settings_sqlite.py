from .settings_base import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/should_not_be_accessed",
    },
}

DATABASES["replica"] = DATABASES["default"].copy()
DATABASES["replica"]["NAME"] += '_replica'
