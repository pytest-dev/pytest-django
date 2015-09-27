import pytest
from django.conf import settings

from pytest_django_test.compat import force_text


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


@pytest.mark.urls('pytest_django_test.urls_overridden')
def test_urls():
    assert settings.ROOT_URLCONF == 'pytest_django_test.urls_overridden'
    assert is_valid_path('/overridden_url/')


@pytest.mark.urls('pytest_django_test.urls_overridden')
def test_urls_client(client):
    response = client.get('/overridden_url/')
    assert force_text(response.content) == 'Overridden urlconf works!'


def test_urls_cache_is_cleared(testdir):
    testdir.makepyfile(myurls="""
        try:
            from django.conf.urls import patterns, url
        except ImportError:
            from django.conf.urls.defaults import patterns, url

        def fake_view(request):
            pass

        urlpatterns = patterns('', url(r'first/$', fake_view, name='first'))
    """)

    testdir.makepyfile("""
        from django.core.urlresolvers import reverse, NoReverseMatch
        import pytest

        @pytest.mark.urls('myurls')
        def test_something():
            reverse('first')

        def test_something_else():
            with pytest.raises(NoReverseMatch):
                reverse('first')
    """)

    result = testdir.runpytest()
    assert result.ret == 0
