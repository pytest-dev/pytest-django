from pytest_django_test.settings_base import *  # noqa

# This is a SQLite configuration, which uses a file based database for
# tests (via setting TEST_NAME / TEST['NAME']).

# The name as expected / used by Django/pytest_django (tests/db_helpers.py).
import tempfile
import os

db_name = 'pytest_django' + db_suffix
test_db_name = 'test_' + db_name
_tmpdir = tempfile.mkdtemp()


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/should_never_be_accessed',
        'TEST': {'NAME': os.path.join(_tmpdir, test_db_name)},
    },
}