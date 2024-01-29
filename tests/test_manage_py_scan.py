import pytest

from .helpers import DjangoPytester


@pytest.mark.django_project(project_root="django_project_root", create_manage_py=True)
def test_django_project_found(django_pytester: DjangoPytester) -> None:
    # XXX: Important: Do not chdir() to django_project_root since runpytest_subprocess
    # will call "python /path/to/pytest.py", which will implicitly add cwd to
    # the path. By instead calling "python /path/to/pytest.py
    # django_project_root", we avoid implicitly adding the project to sys.path
    # This matches the behaviour when pytest is called directly as an
    # executable (cwd is not added to the Python path)

    django_pytester.create_test_module(
        """
    def test_foobar():
        assert 1 + 1 == 2
    """
    )

    result = django_pytester.runpytest_subprocess("django_project_root")
    assert result.ret == 0

    outcomes = result.parseoutcomes()
    assert outcomes["passed"] == 1


@pytest.mark.django_project(project_root="django_project_root", create_manage_py=True)
def test_django_project_found_with_k(
    django_pytester: DjangoPytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that cwd is checked as fallback with non-args via '-k foo'."""
    testfile = django_pytester.create_test_module(
        """
    def test_foobar():
        assert True
    """,
        "sub/test_in_sub.py",
    )

    monkeypatch.chdir(testfile.parent)
    result = django_pytester.runpytest_subprocess("-k", "test_foobar")
    assert result.ret == 0

    outcomes = result.parseoutcomes()
    assert outcomes["passed"] == 1


@pytest.mark.django_project(project_root="django_project_root", create_manage_py=True)
def test_django_project_found_with_k_and_cwd(
    django_pytester: DjangoPytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover cwd not used as fallback if present already in args."""
    testfile = django_pytester.create_test_module(
        """
    def test_foobar():
        assert True
    """,
        "sub/test_in_sub.py",
    )

    monkeypatch.chdir(testfile.parent)
    result = django_pytester.runpytest_subprocess(testfile.parent, "-k", "test_foobar")
    assert result.ret == 0

    outcomes = result.parseoutcomes()
    assert outcomes["passed"] == 1


@pytest.mark.django_project(project_root="django_project_root", create_manage_py=True)
def test_django_project_found_absolute(
    django_pytester: DjangoPytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """This only tests that "." is added as an absolute path (#637)."""
    django_pytester.create_test_module(
        """
    def test_dot_not_in_syspath():
        import sys
        assert '.' not in sys.path[:5]
    """
    )
    monkeypatch.chdir("django_project_root")
    # NOTE: the "." here is important to test for an absolute path being used.
    result = django_pytester.runpytest_subprocess("-s", ".")
    assert result.ret == 0

    outcomes = result.parseoutcomes()
    assert outcomes["passed"] == 1


@pytest.mark.django_project(project_root="django_project_root", create_manage_py=True)
def test_django_project_found_invalid_settings(
    django_pytester: DjangoPytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "DOES_NOT_EXIST")

    result = django_pytester.runpytest_subprocess("django_project_root")
    assert result.ret != 0

    result.stderr.fnmatch_lines(["*ImportError:*DOES_NOT_EXIST*"])
    result.stderr.fnmatch_lines(["*pytest-django found a Django project*"])


def test_django_project_scan_disabled_invalid_settings(
    django_pytester: DjangoPytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "DOES_NOT_EXIST")

    django_pytester.makeini(
        """
    [pytest]
    django_find_project = false
    """
    )

    result = django_pytester.runpytest_subprocess("django_project_root")
    assert result.ret != 0

    result.stderr.fnmatch_lines(["*ImportError*DOES_NOT_EXIST*"])
    result.stderr.fnmatch_lines(["*pytest-django did not search for " "Django projects*"])


@pytest.mark.django_project(project_root="django_project_root", create_manage_py=True)
def test_django_project_found_invalid_settings_version(
    django_pytester: DjangoPytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid DSM should not cause an error with --help or --version."""
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "DOES_NOT_EXIST")

    result = django_pytester.runpytest_subprocess("django_project_root", "--version", "--version")
    assert result.ret == 0

    result.stdout.fnmatch_lines(["*This is pytest version*"])

    result = django_pytester.runpytest_subprocess("django_project_root", "--help")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*usage:*"])


@pytest.mark.django_project(project_root="django_project_root", create_manage_py=True)
def test_django_project_late_settings_version(
    django_pytester: DjangoPytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Late configuration should not cause an error with --help or --version."""
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")
    django_pytester.makepyfile(
        t="WAT = 1",
    )
    django_pytester.makeconftest(
        """
        import os

        def pytest_configure():
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 't')
            from django.conf import settings
            settings.WAT
        """
    )

    result = django_pytester.runpytest_subprocess("django_project_root", "--version", "--version")
    assert result.ret == 0

    result.stdout.fnmatch_lines(["*This is pytest version*"])

    result = django_pytester.runpytest_subprocess("django_project_root", "--help")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*usage:*"])


@pytest.mark.django_project(project_root="django_project_root", create_manage_py=True)
def test_runs_without_error_on_long_args(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
    def test_this_is_a_long_message_which_caused_a_bug_when_scanning_for_manage_py_12346712341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234112341234112451234123412341234123412341234123412341234123412341234123412341234123412341234123412341234():
        assert 1 + 1 == 2
        """
    )

    result = django_pytester.runpytest_subprocess(
        "-k",
        "this_is_a_long_message_which_caused_a_bug_when_scanning_for_manage_py_12346712341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234123412341234112341234112451234123412341234123412341234123412341234123412341234123412341234123412341234123412341234",
        "django_project_root",
    )
    assert result.ret == 0
