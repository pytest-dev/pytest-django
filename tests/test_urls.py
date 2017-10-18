import pytest
from django.conf import settings
from django.utils.encoding import force_text


@pytest.mark.urls('pytest_django_test.urls_overridden')
def test_urls():
    try:
        from django.urls import is_valid_path
    except ImportError:
        from django.core.urlresolvers import is_valid_path
    assert settings.ROOT_URLCONF == 'pytest_django_test.urls_overridden'
    assert is_valid_path('/overridden_url/')


@pytest.mark.urls('pytest_django_test.urls_overridden')
def test_urls_client(client):
    response = client.get('/overridden_url/')
    assert force_text(response.content) == 'Overridden urlconf works!'


def test_urls_cache_is_cleared(testdir):
    testdir.makepyfile(myurls="""
        from django.conf.urls import url
        from pytest_django_test.compat import patterns

        def fake_view(request):
            pass

        urlpatterns = patterns('', url(r'first/$', fake_view, name='first'))
    """)

    testdir.makepyfile("""
        try:
            from django.urls import reverse, NoReverseMatch
        except ImportError:  # Django < 2.0
            from django.core.urlresolvers import reverse, NoReverseMatch
        import pytest

        @pytest.mark.urls('myurls')
        def test_something():
            reverse('first')


        def test_something_else():
            with pytest.raises(NoReverseMatch):
                reverse('first')

    """)

    result = testdir.runpytest_subprocess()
    assert result.ret == 0


def test_urls_cache_is_cleared_and_new_urls_can_be_assigned(testdir):
    testdir.makepyfile(myurls="""
        from django.conf.urls import url
        from pytest_django_test.compat import patterns

        def fake_view(request):
            pass

        urlpatterns = patterns('', url(r'first/$', fake_view, name='first'))
    """)

    testdir.makepyfile(myurls2="""
        from django.conf.urls import url
        from pytest_django_test.compat import patterns

        def fake_view(request):
            pass

        urlpatterns = patterns('', url(r'second/$', fake_view, name='second'))
    """)

    testdir.makepyfile("""
        try:
            from django.urls import reverse, NoReverseMatch
        except ImportError:  # Django < 2.0
            from django.core.urlresolvers import reverse, NoReverseMatch
        import pytest

        @pytest.mark.urls('myurls')
        def test_something():
            reverse('first')

        @pytest.mark.urls('myurls2')
        def test_something_else():
            with pytest.raises(NoReverseMatch):
                reverse('first')

            reverse('second')
    """)

    result = testdir.runpytest_subprocess()
    assert result.ret == 0
