"""
Tests the dynamic loading of all Django assertion cases.
"""

from __future__ import annotations

import inspect

import django.test
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


def test_fixture_assert(django_testcase: django.test.TestCase) -> None:
    django_testcase.assertEqual("a", "a")  # noqa: PT009

    with pytest.raises(AssertionError):
        django_testcase.assertXMLEqual("a" * 10_000, "a")


class TestDjangoAssert(django.test.TestCase):
    def test_fixture_assert(self, django_testcase: django.test.TestCase) -> None:
        assert django_test == self
        django_testcase.assertEqual("a", "a")  # noqa: PT009

        with pytest.raises(AssertionError):
            django_testcase.assertXMLEqual("a" * 10_000, "a")


class TestInternalDjangoAssert:
    def test_fixture_assert(self, django_testcase: django.test.TestCase) -> None:
        django_testcase.assertEqual("a", "a")  # noqa: PT009
        assert not hasattr(self, "assertEqual")

        with pytest.raises(AssertionError):
            django_testcase.assertXMLEqual("a" * 10_000, "a")


@pytest.mark.django_project(create_manage_py=True)
def test_unittest_assert(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        import unittest

        class TestUnittestAssert(unittest.TestCase):
            def test_fixture_assert(self, django_testcase: unittest.TestCase) -> None:
                assert False

            def test_normal_assert(self) -> None:
                self.assertEqual("a", "a")
        """
    )
    result = django_pytester.runpytest_subprocess()
    result.assert_outcomes(failed=1, passed=1)
    assert "missing 1 required positional argument: 'django_testcase'" in result.stdout.str()
