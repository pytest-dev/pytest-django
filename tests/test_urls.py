import pytest
from django.conf import settings
from django.urls import is_valid_path
from django.utils.encoding import force_str


@pytest.mark.urls("pytest_django_test.urls_overridden")
def test_urls() -> None:
    assert settings.ROOT_URLCONF == "pytest_django_test.urls_overridden"
    assert is_valid_path("/overridden_url/")


@pytest.mark.urls("pytest_django_test.urls_overridden")
def test_urls_client(client) -> None:
    response = client.get("/overridden_url/")
    assert force_str(response.content) == "Overridden urlconf works!"


def test_urls_cache_is_cleared(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        myurls="""
        from django.urls import path

        def fake_view(request):
            pass

        urlpatterns = [path('first', fake_view, name='first')]
    """
    )

    pytester.makepyfile(
        """
        from django.urls import reverse, NoReverseMatch
        import pytest

        @pytest.mark.urls('myurls')
        def test_something():
            reverse('first')


        def test_something_else():
            with pytest.raises(NoReverseMatch):
                reverse('first')

    """
    )

    result = pytester.runpytest_subprocess()
    assert result.ret == 0


def test_urls_cache_is_cleared_and_new_urls_can_be_assigned(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        myurls="""
        from django.urls import path

        def fake_view(request):
            pass

        urlpatterns = [path('first', fake_view, name='first')]
    """
    )

    pytester.makepyfile(
        myurls2="""
        from django.urls import path

        def fake_view(request):
            pass

        urlpatterns = [path('second', fake_view, name='second')]
    """
    )

    pytester.makepyfile(
        """
        from django.urls import reverse, NoReverseMatch
        import pytest

        @pytest.mark.urls('myurls')
        def test_something():
            reverse('first')

        @pytest.mark.urls('myurls2')
        def test_something_else():
            with pytest.raises(NoReverseMatch):
                reverse('first')

            reverse('second')
    """
    )

    result = pytester.runpytest_subprocess()
    assert result.ret == 0
