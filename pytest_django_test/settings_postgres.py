from pytest_django_test.settings_base import *  # noqa

# PyPy compatibility
try:
    from psycopg2ct import compat

    compat.register()
except ImportError:
    pass


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "pytest_django" + db_suffix,  # noqa
        "HOST": "localhost",
        "USER": "",
    }
}
