# coding: utf-8
import pytest


def test_django_asserts_available():
    assert hasattr(pytest.django, 'assertTemplateUsed')


def test_sanity():
    from pytest.django import assertJSONEqual

    assertJSONEqual('{}', '{}')
    with pytest.raises(AssertionError):
        assertJSONEqual('{}', '{"a": "1"}')
