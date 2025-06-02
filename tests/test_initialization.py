from textwrap import dedent

import pytest

from .helpers import DjangoPytester


def test_django_setup_order_and_uniqueness(
    django_pytester: DjangoPytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The django.setup() function shall not be called multiple times by
    pytest-django, since it resets logging conf each time.
    """
    django_pytester.makeconftest(
        """
        import django.apps
        assert django.apps.apps.ready
        from tpkg.app.models import Item

        print("conftest")
        def pytest_configure():
            import django
            print("pytest_configure: conftest")
            django.setup = lambda: SHOULD_NOT_GET_CALLED
    """
    )

    django_pytester.project_root.joinpath("tpkg", "plugin.py").write_text(
        dedent(
            """
        import pytest
        import django.apps
        assert not django.apps.apps.ready

        print("plugin")
        def pytest_configure():
            assert django.apps.apps.ready
            from tpkg.app.models import Item
            print("pytest_configure: plugin")

        @pytest.hookimpl(tryfirst=True)
        def pytest_load_initial_conftests(early_config, parser, args):
            print("pytest_load_initial_conftests")
            assert not django.apps.apps.ready
    """
        )
    )
    django_pytester.makepyfile(
        """
        def test_ds():
            pass
    """
    )
    result = django_pytester.runpytest_subprocess("-s", "-p", "tpkg.plugin")
    result.stdout.fnmatch_lines(
        [
            "plugin",
            "pytest_load_initial_conftests",
            "conftest",
            "pytest_configure: conftest",
            "pytest_configure: plugin",
            "* 1 passed*",
        ]
    )
    assert result.ret == 0
