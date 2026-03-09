from textwrap import dedent

import pytest

from .helpers import DjangoPytester


def test_django_setup_order_and_uniqueness(django_pytester: DjangoPytester) -> None:
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


@pytest.mark.parametrize("flag", ["--help", "--version"])
def test_django_setup_for_help_and_version_with_model_import(
    django_pytester: DjangoPytester,
    flag: str,
) -> None:
    """Django should be set up before conftest files are loaded, even with
    --help/--version, so that top-level model imports in conftest files
    don't fail with AppRegistryNotReady.

    Regression test for https://github.com/pytest-dev/pytest-django/issues/1152
    """
    django_pytester.makeconftest(
        """
        from tpkg.app.models import Item
    """
    )

    django_pytester.makepyfile(
        """
        def test_placeholder():
            pass
    """
    )

    args = [flag]
    if flag == "--version":
        # pytest requires -V passed twice to actually print version info
        args.append(flag)

    result = django_pytester.runpytest_subprocess(*args)
    assert result.ret == 0
    result.stderr.no_fnmatch_line("*AppRegistryNotReady*")
    result.stderr.no_fnmatch_line("*could not load initial conftests*")
