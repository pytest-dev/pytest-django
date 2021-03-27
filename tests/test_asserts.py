"""
Tests the dynamic loading of all Django assertion cases.
"""
import inspect

import pytest
import pytest_django

from pytest_django.asserts import __all__ as asserts_all


def _get_actual_assertions_names():
    """
    Returns list with names of all assertion helpers in Django.
    """
    from django.test import TestCase as DjangoTestCase
    from unittest import TestCase as DefaultTestCase

    obj = DjangoTestCase('run')

    def is_assert(func):
        return func.startswith('assert') and '_' not in func

    base_methods = [name for name, member in
                    inspect.getmembers(DefaultTestCase)
                    if is_assert(name)]

    return [name for name, member in inspect.getmembers(obj)
            if is_assert(name) and name not in base_methods]


def test_django_asserts_available():
    django_assertions = _get_actual_assertions_names()
    expected_assertions = asserts_all
    assert set(django_assertions) == set(expected_assertions)

    for name in expected_assertions:
        assert hasattr(pytest_django.asserts, name)


@pytest.mark.django_db
def test_sanity():
    from django.http import HttpResponse
    from pytest_django.asserts import assertContains, assertNumQueries

    response = HttpResponse('My response')

    assertContains(response, 'My response')
    with pytest.raises(AssertionError):
        assertContains(response, 'Not my response')

    assertNumQueries(0, lambda: 1 + 1)
    with assertNumQueries(0):
        pass

    assert assertContains.__doc__
