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
    if 'django' in sys.modules or os.environ.get('DJANGO_SETTINGS_MODULE'):
        from django.conf import settings
        return settings.configured
    else:
        return False
