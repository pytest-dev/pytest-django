import pytest


@pytest.fixture
def no_ds(monkeypatch) -> None:
    """Ensure DJANGO_SETTINGS_MODULE is unset"""
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")


pytestmark = pytest.mark.usefixtures("no_ds")


def test_no_ds(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import os

        def test_env():
            assert 'DJANGO_SETTINGS_MODULE' not in os.environ

        def test_cfg(pytestconfig):
            assert pytestconfig.option.ds is None
    """
    )
    r = pytester.runpytest_subprocess()
    assert r.ret == 0


def test_database(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.django_db
        def test_mark():
            assert 0

        @pytest.mark.django_db(transaction=True)
        def test_mark_trans():
            assert 0

        def test_db(db):
            assert 0

        def test_transactional_db(transactional_db):
            assert 0
    """
    )
    r = pytester.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(["*4 skipped*"])


def test_client(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_client(client):
            assert 0

        def test_admin_client(admin_client):
            assert 0
    """
    )
    r = pytester.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(["*2 skipped*"])


def test_rf(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_rf(rf):
            assert 0
    """
    )
    r = pytester.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(["*1 skipped*"])


def test_settings(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_settings(settings):
            assert 0
    """
    )
    r = pytester.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(["*1 skipped*"])


def test_live_server(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_live_server(live_server):
            assert 0
    """
    )
    r = pytester.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(["*1 skipped*"])


def test_urls_mark(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.urls('foo.bar')
        def test_urls():
            assert 0
    """
    )
    r = pytester.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(["*1 skipped*"])
