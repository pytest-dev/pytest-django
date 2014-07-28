# coding: utf-8
import inspect

import pytest

from pytest_django.lazy_django import get_django_version
from pytest_django.plugin import DJANGO_ASSERTS


def _get_actual_assertions_names():
    """
    Returns list with names of all assertion helpers in Django.
    """
    from django.test import TestCase as DjangoTestCase
    from django.utils.unittest import TestCase as DefaultTestCase

    obj = DjangoTestCase('run')
    is_assert = lambda x: x.startswith('assert') and '_' not in x
    base_methods = [name for name, member in inspect.getmembers(DefaultTestCase)
                    if is_assert(name)]

    return [name for name, member in inspect.getmembers(obj)
            if is_assert(name) and name not in base_methods]


def test_django_asserts_available():
    django_assertions = _get_actual_assertions_names()
    expected_assertions = DJANGO_ASSERTS[get_django_version()[:2]]
    assert not set(django_assertions) ^ set(expected_assertions)

    for name in expected_assertions:
        assert hasattr(pytest.django, name)
