"""Tests which check the various ways you can set DJANGO_SETTINGS_MODULE

If these tests fail you probably forgot to install django-configurations.
"""
import pytest


pytest.importorskip("configurations")


BARE_SETTINGS = """
from configurations import Configuration

class MySettings(Configuration):
    # At least one database must be configured
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        },
    }

    SECRET_KEY = 'foobar'
"""


def test_dc_env(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tpkg.settings_env")
    monkeypatch.setenv("DJANGO_CONFIGURATION", "MySettings")

    pkg = pytester.mkpydir("tpkg")
    settings = pkg.joinpath("settings_env.py")
    settings.write_text(BARE_SETTINGS)
    pytester.makepyfile(
        """
        import os

        def test_settings():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_env'
            assert os.environ['DJANGO_CONFIGURATION'] == 'MySettings'
    """
    )
    result = pytester.runpytest_subprocess()
    result.stdout.fnmatch_lines(
        [
            "django: version: *, settings: tpkg.settings_env (from env), "
            "configuration: MySettings (from env)",
            "* 1 passed*",
        ]
    )
    assert result.ret == 0


def test_dc_env_overrides_ini(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tpkg.settings_env")
    monkeypatch.setenv("DJANGO_CONFIGURATION", "MySettings")

    pytester.makeini(
        """
       [pytest]
       DJANGO_SETTINGS_MODULE = DO_NOT_USE_ini
       DJANGO_CONFIGURATION = DO_NOT_USE_ini
    """
    )
    pkg = pytester.mkpydir("tpkg")
    settings = pkg.joinpath("settings_env.py")
    settings.write_text(BARE_SETTINGS)
    pytester.makepyfile(
        """
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_env'
            assert os.environ['DJANGO_CONFIGURATION'] == 'MySettings'
    """
    )
    result = pytester.runpytest_subprocess()
    result.stdout.fnmatch_lines(
        [
            "django: version: *, settings: tpkg.settings_env (from env), "
            "configuration: MySettings (from env)",
            "* 1 passed*",
        ]
    )
    assert result.ret == 0


def test_dc_ini(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")

    pytester.makeini(
        """
       [pytest]
       DJANGO_SETTINGS_MODULE = tpkg.settings_ini
       DJANGO_CONFIGURATION = MySettings
    """
    )
    pkg = pytester.mkpydir("tpkg")
    settings = pkg.joinpath("settings_ini.py")
    settings.write_text(BARE_SETTINGS)
    pytester.makepyfile(
        """
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_ini'
            assert os.environ['DJANGO_CONFIGURATION'] == 'MySettings'
    """
    )
    result = pytester.runpytest_subprocess()
    result.stdout.fnmatch_lines(
        [
            "django: version: *, settings: tpkg.settings_ini (from ini), "
            "configuration: MySettings (from ini)",
            "* 1 passed*",
        ]
    )
    assert result.ret == 0


def test_dc_option(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "DO_NOT_USE_env")
    monkeypatch.setenv("DJANGO_CONFIGURATION", "DO_NOT_USE_env")

    pytester.makeini(
        """
       [pytest]
       DJANGO_SETTINGS_MODULE = DO_NOT_USE_ini
       DJANGO_CONFIGURATION = DO_NOT_USE_ini
    """
    )
    pkg = pytester.mkpydir("tpkg")
    settings = pkg.joinpath("settings_opt.py")
    settings.write_text(BARE_SETTINGS)
    pytester.makepyfile(
        """
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_opt'
            assert os.environ['DJANGO_CONFIGURATION'] == 'MySettings'
    """
    )
    result = pytester.runpytest_subprocess("--ds=tpkg.settings_opt", "--dc=MySettings")
    result.stdout.fnmatch_lines(
        [
            "django: version: *, settings: tpkg.settings_opt (from option),"
            " configuration: MySettings (from option)",
            "* 1 passed*",
        ]
    )
    assert result.ret == 0
