import pytest

from app.models import Item

from pytest_django import transaction_test_case


def _test_load_fixtures():
    pytest.load_fixture('items')
    assert Item.objects.count() == 1
    assert Item.objects.all()[0].name == 'Fixture item'


def test_load_fixtures():
    _test_load_fixtures()


def test_load_fixtures_again():
    """Ensure fixtures are only loaded once."""
    _test_load_fixtures()


@transaction_test_case
def test_load_fixtures_transaction():
    _test_load_fixtures()


@transaction_test_case
def test_load_fixtures_transaction_again():
    _test_load_fixtures()
