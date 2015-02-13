import pytest
from django.conf import settings

from pytest_django_test.compat import force_text

pytestmark = pytest.mark.urls('pytest_django_test.urls_overridden')

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


def test_urls():
    assert settings.ROOT_URLCONF == 'pytest_django_test.urls_overridden'
    assert is_valid_path('/overridden_url/')


def test_urls_client(client):
    response = client.get('/overridden_url/')
    assert force_text(response.content) == 'Overridden urlconf works!'
