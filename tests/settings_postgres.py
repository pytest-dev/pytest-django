from tests.settings_base import *

# PyPy compatibility
try:
    from psycopg2ct import compat
    compat.register()
except ImportError:
    pass


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pytest_django',
        'HOST': None,
        #'HOST': 'localhost',
        'USER': '',
    },
}
