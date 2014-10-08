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
    setup_django()
    return True


def get_django_version():
    return __import__('django').VERSION


_django_setup_done = False


def setup_django():
    global _django_setup_done
    import django

    if _django_setup_done:
        return

    if hasattr(django, 'setup'):
        django.setup()
    else:
        # Emulate Django 1.7 django.setup() with get_models
        from django.db.models import get_models

        get_models()

    _django_setup_done = True
