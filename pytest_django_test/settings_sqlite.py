from .settings_base import *  # noqa: F401 F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/should_not_be_accessed",
    },
    "two": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/should_not_be_accessed_two",
        "TEST": {
            "PYTEST_DJANGO_ALLOW_TRANSACTIONS": True
        }
    }
}
