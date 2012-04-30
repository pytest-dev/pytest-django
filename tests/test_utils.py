from django.core.urlresolvers import is_valid_path
from django.conf import settings

from app.models import Item

import pytest


def test_load_fixtures():
    pytest.load_fixture('items')
    assert Item.objects.count() == 1
    assert Item.objects.all()[0].name == 'Fixture item'


def test_load_fixtures_again():
    """Ensure fixtures are only loaded once."""
    test_load_fixtures()


@pytest.urls('tests.urls_overridden')
def test_urls(client):
    assert settings.ROOT_URLCONF == 'tests.urls_overridden'
    assert is_valid_path('/overridden_url/')

    response = client.get('/overridden_url/')

    assert response.content == 'Overridden urlconf works!'
