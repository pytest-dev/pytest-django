import pytest


@pytest.fixture
def no_ds(monkeypatch):
    """Ensure DJANGO_SETTINGS_MODULE is unset"""
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE')


pytestmark = pytest.mark.usefixtures('no_ds')


def test_no_ds(testdir):
    testdir.makepyfile("""
        import os

        def test_env():
            assert 'DJANGO_SETTINGS_MODULE' not in os.environ

        def test_cfg(pytestconfig):
            assert pytestconfig.option.ds is None
    """)
    r = testdir.runpytest_subprocess()
    assert r.ret == 0


def test_database(testdir):
    testdir.makepyfile("""
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
    """)
    r = testdir.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(['*4 skipped*'])


def test_client(testdir):
    testdir.makepyfile("""
        def test_client(client):
            assert 0

        def test_admin_client(admin_client):
            assert 0
    """)
    r = testdir.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(['*2 skipped*'])


def test_rf(testdir):
    testdir.makepyfile("""
        def test_rf(rf):
            assert 0
    """)
    r = testdir.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(['*1 skipped*'])


def test_settings(testdir):
    testdir.makepyfile("""
        def test_settings(settings):
            assert 0
    """)
    r = testdir.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(['*1 skipped*'])


def test_live_server(testdir):
    testdir.makepyfile("""
        def test_live_server(live_server):
            assert 0
    """)
    r = testdir.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(['*1 skipped*'])


def test_urls_mark(testdir):
    testdir.makepyfile("""
        import pytest

        @pytest.mark.urls('foo.bar')
        def test_urls():
            assert 0
    """)
    r = testdir.runpytest_subprocess()
    assert r.ret == 0
    r.stdout.fnmatch_lines(['*1 skipped*'])
