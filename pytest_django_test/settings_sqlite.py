from .settings_base import *  # noqa: F401 F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/should_not_be_accessed",
    }
}
