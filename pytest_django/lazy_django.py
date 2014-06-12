"""
Helpers to load Django lazily when Django settings can't be configured.
"""

import os
import sys
import pytest


def skip_if_no_django():
    """Raises a skip exception when no Django settings are available"""
    if not django_settings_is_configured():
        pytest.skip('Test skipped since no Django settings is present.')


def django_settings_is_configured():
    if not os.environ.get('DJANGO_SETTINGS_MODULE') \
            and not 'django' in sys.modules:
        return False

    from django.conf import settings
    if settings.configured:
        return True

    from django.core.exceptions import ImproperlyConfigured
    try:
        settings.DATABASES
    except (ImproperlyConfigured, ImportError):
        e = sys.exc_info()[1]
        raise pytest.UsageError(
            "pytest_django: failed to load Django settings: %s" % (e.args))

    return settings.configured
