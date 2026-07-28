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


@pytest.mark.parametrize("option", ["--help", "--version"])
def test_django_setup_with_help_and_version(
    django_pytester: DjangoPytester,
    option: str,
) -> None:
    """Django must be set up before conftest files are imported, even for
    ``--help``/``--version``, so a top-level Django model import in a
    ``conftest.py`` does not fail with ``AppRegistryNotReady``.

    Regression test for https://github.com/pytest-dev/pytest-django/issues/1152
    """
    django_pytester.makeconftest(
        """
        from tpkg.app.models import Item  # noqa: F401

        # Only reached if the model import above succeeds (i.e. Django is set
        # up). With --version, pytest records but never prints the conftest
        # load failure, so we assert on this positive marker instead.
        print("conftest-imported-models")
    """
    )

    # A single `--version`/`-V` is short-circuited before pytest loads any
    # conftests (pytest #13574), so it wouldn't exercise this path; passing
    # it twice forces full startup, which imports the initial conftests.
    args = [option, option] if option == "--version" else [option]
    result = django_pytester.runpytest_subprocess(*args)

    # `--help` writes its own output around the conftest's, so the marker does
    # not necessarily end up on a line of its own.
    result.stdout.fnmatch_lines(["*conftest-imported-models*"])
    result.stdout.no_fnmatch_line("*AppRegistryNotReady*")
    result.stdout.no_fnmatch_line("*could not load initial conftests*")
    assert result.ret == 0


def test_help_with_unusable_configuration(django_pytester: DjangoPytester) -> None:
    """Setting Django up for ``--help``/``--version`` must not make them depend
    on a usable configuration, no matter where the initialization fails.

    ``test_manage_py_scan.py`` covers an invalid ``DJANGO_SETTINGS_MODULE``
    (issue #235); this covers a failure which is neither an ``ImportError`` nor
    related to the settings module.
    """
    django_pytester.makeini(
        """
        [pytest]
        django_find_project = not-a-bool
        """
    )

    result = django_pytester.runpytest_subprocess("--help")

    result.stdout.fnmatch_lines(["*usage:*"])
    assert result.ret == 0
