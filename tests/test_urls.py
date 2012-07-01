try:
    from django.core.urlresolvers import is_valid_path
    is_valid_path  # Avoid pyflakes warning
except ImportError:
    from django.core.urlresolvers import resolve, Resolver404

    def is_valid_path(path, urlconf=None):
        """
        Returns True if the given path resolves against the default URL resolver,
        False otherwise.

        This is a convenience method to make working with "is this a match?" cases
        easier, avoiding unnecessarily indented try...except blocks.
        """
        try:
            resolve(path, urlconf)
            return True
        except Resolver404:
            return False


from django.conf import settings

import pytest


@pytest.urls('tests.urls_overridden')
def test_urls(client):
    assert settings.ROOT_URLCONF == 'tests.urls_overridden'
    assert is_valid_path('/overridden_url/')

    response = client.get('/overridden_url/')

    assert response.content == 'Overridden urlconf works!'


@pytest.mark.urls('tests.urls_overridden')
def test_urls_mark(client):
    test_urls(client)
