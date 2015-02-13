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
    # Avoid importing Django if it has not yet been imported
    if not os.environ.get('DJANGO_SETTINGS_MODULE') \
            and 'django' not in sys.modules:
        return False

    # If DJANGO_SETTINGS_MODULE is defined at this point, Django is assumed to
    # always be loaded.
    from django.conf import settings
    assert settings.configured is True
    return True


def get_django_version():
    return __import__('django').VERSION
