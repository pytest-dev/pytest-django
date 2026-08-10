from .helpers import DjangoPytester


def test_django_isolate_apps_marker(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        import pytest
        from django.apps import apps


        @pytest.mark.django_isolate_apps("tpkg.app")
        def test_isolated_registry_fixture(django_isolated_apps):
            assert django_isolated_apps.is_installed("tpkg.app")
            assert not django_isolated_apps.is_installed("django.contrib.auth")


        @pytest.mark.django_isolate_apps("tpkg.app", "django.contrib.auth")
        def test_isolated_registry_multiple_apps(django_isolated_apps):
            assert django_isolated_apps.is_installed("tpkg.app")
            assert django_isolated_apps.is_installed("django.contrib.auth")


        @pytest.mark.django_isolate_apps("tpkg.app")
        class TestIsolatedRegistryClass:
            def test_first(self, django_isolated_apps):
                assert django_isolated_apps.is_installed("tpkg.app")

            def test_second(self, django_isolated_apps):
                assert not django_isolated_apps.is_installed("django.contrib.auth")


        @pytest.mark.django_isolate_apps("tpkg.app")
        def test_global_registry_is_unchanged():
            assert apps.is_installed("django.contrib.auth")
        """
    )

    result = django_pytester.runpytest_subprocess("-v")
    result.assert_outcomes(passed=5)


def test_django_isolate_apps_is_functional(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        import pytest
        from django.db import models
        from django.apps import apps


        @pytest.mark.django_db
        @pytest.mark.django_isolate_apps("tpkg.app")
        def test_model_is_registered(django_isolated_apps):
            class MyModel(models.Model):
                class Meta:
                    app_label = "app"

            assert django_isolated_apps.get_model('app', 'MyModel') is not None

            with pytest.raises(LookupError):
                apps.get_model('app', 'MyModel')
        """
    )
    result = django_pytester.runpytest_subprocess("-v")
    result.assert_outcomes(passed=1)


def test_django_isolate_apps_marker_requires_labels(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        import pytest


        @pytest.mark.django_isolate_apps()
        def test_isolated_registry_requires_labels():
            pass
        """
    )

    result = django_pytester.runpytest_subprocess("-v")
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        ["*ValueError: @pytest.mark.django_isolate_apps requires at least one app label*"]
    )


def test_django_isolated_apps_fixture_requires_marker(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        def test_requires_marker(django_isolated_apps):
            pass
        """
    )

    result = django_pytester.runpytest_subprocess("-v")
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        [
            "*UsageError: The django_isolated_apps fixture requires @pytest.mark.django_isolate_apps*"
        ]
    )
