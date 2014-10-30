import pytest

from pytest_django.django_compat import is_django_unittest

from django.test import TestCase


@pytest.fixture(scope="session", autouse=True)
def check_is_django_unitttest(request):
    for item in request.node.items:
        if hasattr(item, 'cls') and item.cls == TestSimple:
            assert is_django_unittest(item)


class TestSimple(TestCase):
    def test_nothing(self):
        pass
