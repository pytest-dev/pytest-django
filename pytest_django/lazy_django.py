"""
Helpers to load Django lazily when DJANGO_SETTINGS_MODULE is not defined.
"""

import os

import pytest


def skip_if_no_django():
    """Raises a skip exception when no Django settings are available"""
    if not django_settings_is_configured():
        pytest.skip('Test skipped since DJANGO_SETTINGS_MODULE is not defined.')


def django_settings_is_configured():
    return bool(os.environ.get('DJANGO_SETTINGS_MODULE'))
