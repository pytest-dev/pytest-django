from django.conf import settings
from django.test.utils import get_runner


_runner = get_runner(settings)(interactive=False)


def _setup_databases(verbosity=0, interactive=False):
    return _runner.setup_databases()

setup_databases = _setup_databases
teardown_databases = _runner.teardown_databases

setup_test_environment = _runner.setup_test_environment
teardown_test_environment = _runner.teardown_test_environment

try:
    from django import setup
except ImportError:
    # Emulate Django 1.7 django.setup() with get_models
    from django.db.models import get_models as setup
