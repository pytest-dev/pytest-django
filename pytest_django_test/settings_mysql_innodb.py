from .settings_base import *  # noqa: F401 F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "pytest_django_should_never_get_accessed",
        "HOST": "localhost",
        "USER": "root",
        "OPTIONS": {"init_command": "SET default_storage_engine=InnoDB"},
    }
}
