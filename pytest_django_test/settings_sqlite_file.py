from pytest_django_test.settings_base import *  # noqa

# This is a SQLite configuration, which uses a file based database for
# tests (via setting TEST_NAME / TEST['NAME']).

# The name as expected / used by Django/pytest_django (tests/db_helpers.py).
db_name = 'DBNAME_pytest_django_db' + db_suffix
test_db_name = 'test_' + db_name + '_db_test'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': db_name,
        # # Django > (1, 7)
        'TEST': {'NAME': test_db_name},
        # # Django < (1, 7)
        'TEST_NAME': test_db_name,
    },
}
