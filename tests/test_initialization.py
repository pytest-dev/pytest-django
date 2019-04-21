from textwrap import dedent

import pytest


@pytest.mark.parametrize("conftest_mark", ("tryfirst", "trylast"))
def test_django_setup_order_and_uniqueness(conftest_mark, django_testdir, monkeypatch):
    """
    The django.setup() function shall not be called multiple times by
    pytest-django, since it resets logging conf each time.
    """
    django_testdir.makeconftest(
        """
        import pytest
        import django.apps

        print("conftest")

        assert not django.apps.apps.ready

        orig_django_setup = django.setup
        def django_setup(*args, **kwargs):
            print("django_setup")
            orig_django_setup(*args, **kwargs)
        django.setup = django_setup

        @pytest.mark.{conftest_mark}
        def pytest_configure():
            if "{conftest_mark}" == "tryfirst":
                assert not django.apps.apps.ready
            else:
                assert django.apps.apps.ready

            print("pytest_configure: conftest")
        """.format(
            conftest_mark=conftest_mark
        ))

    django_testdir.project_root.join("tpkg", "plugin.py").write(
        dedent(
            """
        import pytest
        import django.apps
        assert not django.apps.apps.ready

        print("plugin")
        def pytest_configure():
            assert not django.apps.apps.ready
            print("pytest_configure: plugin")

        @pytest.hookimpl(hookwrapper=True, tryfirst=True)
        def pytest_load_initial_conftests(early_config, parser, args):
            print("pytest_load_initial_conftests_start")
            assert not django.apps.apps.ready

            yield

            print("pytest_load_initial_conftests_end")
            assert not django.apps.apps.ready
    """
        )
    )
    django_testdir.makepyfile(
        """
        def test_ds():
            pass
    """
    )
    result = django_testdir.runpytest_subprocess("-s", "-p", "tpkg.plugin")

    if conftest_mark == "tryfirst":
        result.stdout.fnmatch_lines(
            [
                "plugin",
                "pytest_load_initial_conftests_start",
                "conftest",
                "pytest_load_initial_conftests_end",
                "pytest_configure: conftest",
                "pytest_configure: plugin",
                "django_setup",
                "*1 passed*",
            ]
        )
    else:
        result.stdout.fnmatch_lines(
            [
                "plugin",
                "pytest_load_initial_conftests_start",
                "conftest",
                "pytest_load_initial_conftests_end",
                "pytest_configure: plugin",
                "django_setup",
                "pytest_configure: conftest",
                "*1 passed*",
            ]
        )

    assert result.ret == 0
