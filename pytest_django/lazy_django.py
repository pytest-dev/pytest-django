"""
Helpers to load Django lazily when Django settings are not able to be configured.
"""

import pytest


def skip_if_no_django():
    """Raises a skip exception when no Django settings are available"""
    if not django_settings_is_configured():
        pytest.skip('Test skipped since DJANGO_SETTINGS_MODULE is not defined.')


def django_settings_is_configured():
    try:
        from django.conf import settings
    except ImportError:
        return False
    return settings.configured
