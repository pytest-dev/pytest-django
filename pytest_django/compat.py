# In Django 1.6, the old test runner was deprecated, and the useful bits were
# moved out of the test runner

def get_runner():
    from django.conf import settings
    parts = settings.TEST_RUNNER.split('.')
    runner_path, runner_class = '.'.join(parts[:-1]), parts[-1]
    module = __import__(runner_path, fromlist=parts[:-2])
    return getattr(module, runner_class)

_runner = get_runner()(interactive=False)


try:
    from django.test.runner import setup_databases
except ImportError:
    setup_databases = _runner.setup_databases

teardown_databases = _runner.teardown_databases

try:
    from django.test.utils import (setup_test_environment,
                                   teardown_test_environment)
except ImportError:
    setup_test_environment = _runner.setup_test_environment
    teardown_test_environment = _runner.teardown_test_environment


del _runner


try:
    from django import setup
except ImportError:
    # Emulate Django 1.7 django.setup() with get_models
    from django.db.models import get_models as setup
