"""
Tests the dynamic loading of all Django assertion cases.
"""

from __future__ import annotations

import inspect

import pytest

from .helpers import DjangoPytester

import pytest_django
from pytest_django.asserts import __all__ as asserts_all


def _get_actual_assertions_names() -> list[str]:
    """
    Returns list with names of all assertion helpers in Django.
    """
    from unittest import TestCase as DefaultTestCase

    from django import VERSION
    from django.test import TestCase as DjangoTestCase

    if VERSION >= (5, 0):
        from django.contrib.messages.test import MessagesTestMixin

        class MessagesTestCase(MessagesTestMixin, DjangoTestCase):
            pass

        obj = MessagesTestCase("run")
    else:
        obj = DjangoTestCase("run")

    def is_assert(func) -> bool:
        return func.startswith("assert") and "_" not in func

    base_methods = [
        name for name, member in inspect.getmembers(DefaultTestCase) if is_assert(name)
    ]

    return [
        name
        for name, member in inspect.getmembers(obj)
        if is_assert(name) and name not in base_methods
    ]


def test_django_asserts_available() -> None:
    django_assertions = _get_actual_assertions_names()
    expected_assertions = asserts_all
    assert set(django_assertions) == set(expected_assertions)

    for name in expected_assertions:
        assert hasattr(pytest_django.asserts, name)


@pytest.mark.django_db
def test_sanity() -> None:
    from django.http import HttpResponse

    from pytest_django.asserts import assertContains, assertNumQueries

    response = HttpResponse("My response")

    assertContains(response, "My response")
    with pytest.raises(AssertionError):
        assertContains(response, "Not my response")

    assertNumQueries(0, lambda: 1 + 1)
    with assertNumQueries(0):
        pass

    assert assertContains.__doc__


def test_assert_diff(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        import pytest_django.asserts

        def test_test_case():
            assert pytest_django.asserts.test_case.maxDiff is not None

        def test_assert():
            pytest_django.asserts.assertXMLEqual("a" * 10_000, "a")
        """
    )
    result = django_pytester.runpytest_subprocess()
    assert "[truncated]... != 'a'" in "\n".join([*result.stdout, *result.stderr])
    result.assert_outcomes(passed=1, errors=1)


def test_assert_diff_verbose(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        import pytest_django.asserts

        def test_test_case():
            assert pytest_django.asserts.test_case.maxDiff is None

        def test_assert():
            pytest_django.asserts.assertXMLEqual("a" * 10_000, "a")
        """
    )
    result = django_pytester.runpytest_subprocess("-v")
    assert "a" * 10_000 in "\n".join([*result.stdout, *result.stderr])
    result.assert_outcomes(passed=1, errors=1)
