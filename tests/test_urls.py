import pytest
from django.conf import settings
from .compat import force_text

try:
    from django.core.urlresolvers import is_valid_path
except ImportError:
    from django.core.urlresolvers import resolve, Resolver404

    def is_valid_path(path, urlconf=None):
        """Return True if path resolves against default URL resolver

        This is a convenience method to make working with "is this a
        match?" cases easier, avoiding unnecessarily indented
        try...except blocks.
        """
        try:
            resolve(path, urlconf)
            return True
        except Resolver404:
            return False


@pytest.mark.urls('tests.urls_overridden')
def test_urls():
    assert settings.ROOT_URLCONF == 'tests.urls_overridden'
    assert is_valid_path('/overridden_url/')


@pytest.mark.urls('tests.urls_overridden')
def test_urls_client(client):
    response = client.get('/overridden_url/')
    assert force_text(response.content) == 'Overridden urlconf works!'
