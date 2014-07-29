import pytest
from django.conf import settings
from .compat import force_text, is_valid_path


@pytest.mark.urls('tests.urls_overridden')
def test_urls():
    assert settings.ROOT_URLCONF == 'tests.urls_overridden'
    assert is_valid_path('/overridden_url/')


@pytest.mark.urls('tests.urls_overridden')
def test_urls_client(client):
    response = client.get('/overridden_url/')
    assert force_text(response.content) == 'Overridden urlconf works!'
