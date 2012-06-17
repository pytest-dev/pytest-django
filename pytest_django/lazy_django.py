"""
Helpers to load Django lazily when DJANGO_SETTINGS_MODULE is not defined.
"""

import os

import pytest


def skip_if_no_django():
    """
    """
    if not django_is_usable():
        pytest.skip('Test skipped since DJANGO_SETTINGS_MODULE is not defined.')


def django_is_usable():
    return bool(os.environ.get('DJANGO_SETTINGS_MODULE'))
