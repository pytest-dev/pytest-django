from django.core.urlresolvers import is_valid_path
from django.conf import settings

import pytest


@pytest.urls('tests.urls_overridden')
def test_urls(client):
    assert settings.ROOT_URLCONF == 'tests.urls_overridden'
    assert is_valid_path('/overridden_url/')

    response = client.get('/overridden_url/')

    assert response.content == 'Overridden urlconf works!'
