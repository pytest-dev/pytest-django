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


def do_django_imports():
    """
    Required django imports for the plugin

    Since django is properly messed up with it's global state and code
    execution at import it is almost impossible to import any part of
    django without having DJANGO_SETTINGS_MODULE set.  Since this
    plugin wants to work without this environment variable set we need
    to delay all django imports.

    For this we access django using py.std.django which does a lazy
    import.  The limitation of py.std is that only the top level
    package is imported, but by importing the sub-packages explicitly
    we let the import machinery create all the sub-module references
    and py.std.django will have all required sub-modules available.
    """
    import django.conf
    import django.contrib.auth.models
    import django.core.management
    import django.core.urlresolvers
    import django.db.backends.util
    import django.test
    import django.test.client
    import django.test.simple
    import django.test.testcases

    django  # Silence pyflakes
