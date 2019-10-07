import os
from textwrap import dedent


def test_python_path_ini_settings(testdir):

    src_dir = testdir.mkdir("src")
    settings_file = src_dir.join("mycustomsettings.py")
    with open(str(settings_file), "w") as f:
        f.write("SECRET_KEY='28769GJSVBZJZVSNBZVZVBZNZB'")

    sitedir = testdir.mkdir("sitedir")
    pth_file = sitedir.join("stuffs.pth")
    with open(str(pth_file), "w") as f:
        f.write("../src")

    testdir.makepyfile(test_stuffs="def test_some_stuffs(): pass")  # Dummy test

    result = testdir.runpytest_subprocess("--ds=mycustomsettings")
    result.stderr.fnmatch_lines(
        [
            "ImportError: No module named *mycustomsettings*"
        ]
    )
    assert result.ret == 1

    testdir.makeini(
        """
       [pytest]
       python_paths_early = src/
                            ~/myhomesubdir/
                            /tmp/path/to/somewhere
        """)

    expected_python_paths = (os.path.normpath(os.path.join(str(testdir), "src/")),
                             os.path.normpath(os.path.join(str(testdir), "myhomesubdir/")),
                             os.path.normpath("/tmp/path/to/somewhere"))
    expected_python_paths_fnmatch = "*early extra python paths: %s*" % str(expected_python_paths)

    result = testdir.runpytest_subprocess("--ds=mycustomsettings")
    result.stdout.fnmatch_lines(
        [
            expected_python_paths_fnmatch,
        ]
    )
    assert result.ret == 0  # Dummy test ran

    testdir.makeini("")  # Erase ini file

    result = testdir.runpytest_subprocess("--ds=mycustomsettings")
    result.stderr.fnmatch_lines(
        [
            "ImportError: No module named *mycustomsettings*"
        ]
    )
    assert result.ret == 1

    testdir.makeini(
        """
       [pytest]
       site_dirs_early = sitedir/
                       ~/myhomesubdir2/
                       /tmp2/path2/to2/somewhere2
        """)

    expected_site_dirs = (os.path.normpath(os.path.join(str(testdir), "sitedir/")),
                          os.path.normpath(os.path.join(str(testdir), "myhomesubdir2/")),
                          os.path.normpath("/tmp2/path2/to2/somewhere2"))
    expected_site_dirs_fnmatch = "*early extra site dirs: %s*" % str(expected_site_dirs)

    result = testdir.runpytest_subprocess("--ds=mycustomsettings")
    result.stdout.fnmatch_lines(
        [
            expected_site_dirs_fnmatch,
        ]
    )
    assert result.ret == 0  # Dummy test ran


def test_django_setup_order_and_uniqueness(django_testdir, monkeypatch):
    """
    The django.setup() function shall not be called multiple times by
    pytest-django, since it resets logging conf each time.
    """
    django_testdir.makeconftest(
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

    django_testdir.project_root.join("tpkg", "plugin.py").write(
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
    django_testdir.makepyfile(
        """
        def test_ds():
            pass
    """
    )
    result = django_testdir.runpytest_subprocess("-s", "-p", "tpkg.plugin")
    result.stdout.fnmatch_lines(
        [
            "plugin",
            "pytest_load_initial_conftests",
            "conftest",
            "pytest_configure: conftest",
            "pytest_configure: plugin",
            "* 1 passed in*",
        ]
    )
    assert result.ret == 0
