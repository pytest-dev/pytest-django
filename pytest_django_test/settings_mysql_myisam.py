from pytest_django_test.settings_base import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "pytest_django" + db_suffix,  # noqa: F405
        "HOST": "localhost",
        "USER": "root",
        "OPTIONS": {"init_command": "SET default_storage_engine=MyISAM"},
    }
}
