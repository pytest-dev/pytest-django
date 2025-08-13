import pytest
from django.conf import settings
from django.urls import is_valid_path
from django.utils.encoding import force_str

from .helpers import DjangoPytester


@pytest.mark.urls("pytest_django_test.urls_overridden")
def test_urls() -> None:
    assert settings.ROOT_URLCONF == "pytest_django_test.urls_overridden"
    assert is_valid_path("/overridden_url/")


@pytest.mark.urls("pytest_django_test.urls_overridden")
def test_urls_client(client) -> None:
    response = client.get("/overridden_url/")
    assert force_str(response.content) == "Overridden urlconf works!"


@pytest.mark.django_project(
    extra_settings="""
    ROOT_URLCONF = "empty"
    """,
)
def test_urls_cache_is_cleared(django_pytester: DjangoPytester) -> None:
    django_pytester.makepyfile(
        empty="""
        urlpatterns = []
        """,
        myurls="""
        from django.urls import path

        def fake_view(request):
            pass

        urlpatterns = [path('first', fake_view, name='first')]
        """,
    )

    django_pytester.create_test_module(
        """
        from django.urls import reverse, NoReverseMatch
        import pytest

        @pytest.mark.urls('myurls')
        def test_something():
            reverse('first')

        def test_something_else():
            with pytest.raises(NoReverseMatch):
                reverse('first')
        """,
    )

    result = django_pytester.runpytest_subprocess()
    assert result.ret == 0


@pytest.mark.django_project(
    extra_settings="""
    ROOT_URLCONF = "empty"
    """,
)
def test_urls_cache_is_cleared_and_new_urls_can_be_assigned(
    django_pytester: DjangoPytester,
) -> None:
    django_pytester.makepyfile(
        empty="""
        urlpatterns = []
        """,
        myurls="""
        from django.urls import path

        def fake_view(request):
            pass

        urlpatterns = [path('first', fake_view, name='first')]
        """,
        myurls2="""
        from django.urls import path

        def fake_view(request):
            pass

        urlpatterns = [path('second', fake_view, name='second')]
        """,
    )

    django_pytester.create_test_module(
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
        """,
    )

    result = django_pytester.runpytest_subprocess()
    assert result.ret == 0


@pytest.mark.django_project(
    extra_settings="""
    ROOT_URLCONF = "empty"
    """
)
def test_urls_concurrent(django_pytester: DjangoPytester) -> None:
    "Test that the URL cache clearing is thread-safe with pytest-xdist."
    pytest.importorskip("xdist")

    django_pytester.makepyfile(
        empty="urlpatterns = []",
        urls1="""
        from django.urls import path
        urlpatterns = [path('url1/', lambda r: None, name='url1')]
        """,
        urls2="""
        from django.urls import path
        urlpatterns = [path('url2/', lambda r: None, name='url2')]
        """,
    )

    django_pytester.create_test_module(
        """
        import pytest
        from django.urls import reverse, NoReverseMatch

        @pytest.mark.urls('urls1')
        def test_urls1():
            reverse('url1')
            with pytest.raises(NoReverseMatch):
                reverse('url2')

        @pytest.mark.urls('urls2')
        def test_urls2():
            reverse('url2')
            with pytest.raises(NoReverseMatch):
                reverse('url1')
        """
    )

    result = django_pytester.runpytest_subprocess("-n", "2")
    assert result.ret == 0
