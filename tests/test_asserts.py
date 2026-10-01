"""
Tests the dynamic loading of all Django assertion cases.
"""

from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import cast

import pytest

import pytest_django
import pytest_django.asserts
from pytest_django.asserts import __all__ as asserts_all


def _get_actual_assertions_names() -> list[str]:
    """
    Returns list with names of all assertion helpers in Django.
    """
    from unittest import TestCase as DefaultTestCase

    from django.contrib.messages.test import MessagesTestMixin
    from django.test import TestCase as DjangoTestCase

    class MessagesTestCase(MessagesTestMixin, DjangoTestCase):
        pass

    obj = MessagesTestCase("run")

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
    expected_assertions = cast(Sequence[str], asserts_all)
    assert set(django_assertions) == set(expected_assertions)

    for name in expected_assertions:
        assert hasattr(pytest_django.asserts, name)


@pytest.mark.django_db
def test_sanity() -> None:
    from django.http import HttpResponse

    from pytest_django.asserts import assertContains, assertNumQueries

    response = HttpResponse(b"My response")

    assertContains(response, b"My response")
    with pytest.raises(AssertionError):
        assertContains(response, b"Not my response")

    assertNumQueries(0, lambda: 1 + 1)
    with assertNumQueries(0):
        pass

    assert assertContains.__doc__


def test_django_asserts_max_diff_can_be_unlimited(
    django_pytester: pytest.Pytester,
) -> None:
    django_pytester.makeini(
        """
        [pytest]
        django_asserts_max_diff = None
        """
    )
    django_pytester.makepyfile(
        """
        from pytest_django.asserts import assertXMLEqual


        def test_assert_xml_equal_uses_the_configured_max_diff():
            expected = "<root>" + "".join(f"<item>{i}</item>" for i in range(100)) + "</root>"
            actual = "<root>" + "".join(f"<item>{i + 1}</item>" for i in range(100)) + "</root>"

            try:
                assertXMLEqual(expected, actual)
            except AssertionError as error:
                assert "Set self.maxDiff to None" not in str(error)
            else:
                raise AssertionError("assertXMLEqual unexpectedly passed")
        """
    )

    result = django_pytester.runpytest_subprocess()

    result.assert_outcomes(passed=1)


def test_django_asserts_max_diff_requires_an_integer_or_none(
    django_pytester: pytest.Pytester,
) -> None:
    django_pytester.makeini(
        """
        [pytest]
        django_asserts_max_diff = unlimited
        """
    )

    result = django_pytester.runpytest_subprocess()

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*django_asserts_max_diff must be an integer or None*"])
