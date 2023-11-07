"""Tests which check the various ways you can set DJANGO_SETTINGS_MODULE

If these tests fail you probably forgot to run "pip install -e .".
"""

import pytest


BARE_SETTINGS = """
# At least one database must be configured
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    },
}
SECRET_KEY = 'foobar'
"""


def test_ds_ini(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")
    pytester.makeini(
        """
       [pytest]
       DJANGO_SETTINGS_MODULE = tpkg.settings_ini
    """
    )
    pkg = pytester.mkpydir("tpkg")
    pkg.joinpath("settings_ini.py").write_text(BARE_SETTINGS)
    pytester.makepyfile(
        """
        import os

        def test_ds():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_ini'
    """
    )
    result = pytester.runpytest_subprocess()
    result.stdout.fnmatch_lines(
        [
            "django: version: *, settings: tpkg.settings_ini (from ini)",
            "*= 1 passed*",
        ]
    )
    assert result.ret == 0


def test_ds_env(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tpkg.settings_env")
    pkg = pytester.mkpydir("tpkg")
    settings = pkg.joinpath("settings_env.py")
    settings.write_text(BARE_SETTINGS)
    pytester.makepyfile(
        """
        import os

        def test_settings():
            assert os.environ['DJANGO_SETTINGS_MODULE'] == 'tpkg.settings_env'
    """
    )
    result = pytester.runpytest_subprocess()
    result.stdout.fnmatch_lines(
        [
            "django: version: *, settings: tpkg.settings_env (from env)",
            "*= 1 passed*",
        ]
    )


def test_ds_option(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "DO_NOT_USE_env")
    pytester.makeini(
        """
       [pytest]
       DJANGO_SETTINGS_MODULE = DO_NOT_USE_ini
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
    """
    )
    result = pytester.runpytest_subprocess("--ds=tpkg.settings_opt")
    result.stdout.fnmatch_lines(
        [
            "django: version: *, settings: tpkg.settings_opt (from option)",
            "*= 1 passed*",
        ]
    )


def test_ds_env_override_ini(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    "DSM env should override ini."
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tpkg.settings_env")
    pytester.makeini(
        """\
       [pytest]
       DJANGO_SETTINGS_MODULE = DO_NOT_USE_ini
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
    """
    )
    result = pytester.runpytest_subprocess()
    assert result.parseoutcomes()["passed"] == 1
    assert result.ret == 0


def test_ds_non_existent(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Make sure we do not fail with INTERNALERROR if an incorrect
    DJANGO_SETTINGS_MODULE is given.
    """
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "DOES_NOT_EXIST")
    pytester.makepyfile("def test_ds(): pass")
    result = pytester.runpytest_subprocess()
    result.stderr.fnmatch_lines(["*ImportError:*DOES_NOT_EXIST*"])
    assert result.ret != 0


def test_ds_after_user_conftest(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test that the settings module can be imported, after pytest has adjusted
    the sys.path.
    """
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "settings_after_conftest")
    pytester.makepyfile("def test_ds(): pass")
    pytester.makepyfile(settings_after_conftest="SECRET_KEY='secret'")
    # pytester.makeconftest("import sys; print(sys.path)")
    result = pytester.runpytest_subprocess("-v")
    result.stdout.fnmatch_lines(["* 1 passed*"])
    assert result.ret == 0


def test_ds_in_pytest_configure(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")
    pkg = pytester.mkpydir("tpkg")
    settings = pkg.joinpath("settings_ds.py")
    settings.write_text(BARE_SETTINGS)
    pytester.makeconftest(
        """
        import os

        from django.conf import settings

        def pytest_configure():
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                                      'tpkg.settings_ds')
    """
    )

    pytester.makepyfile(
        """
        def test_anything():
            pass
    """
    )

    r = pytester.runpytest_subprocess()
    assert r.parseoutcomes()["passed"] == 1
    assert r.ret == 0


def test_django_settings_configure(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Make sure Django can be configured without setting
    DJANGO_SETTINGS_MODULE altogether, relying on calling
    django.conf.settings.configure() and then invoking pytest.
    """
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")

    p = pytester.makepyfile(
        run="""
            from django.conf import settings
            settings.configure(SECRET_KEY='set from settings.configure()',
                               DATABASES={'default': {
                                   'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'
                               }},
                               INSTALLED_APPS=['django.contrib.auth',
                                               'django.contrib.contenttypes',])

            import pytest

            pytest.main()
    """
    )

    pytester.makepyfile(
        """
        import pytest

        from django.conf import settings
        from django.test import RequestFactory, TestCase
        from django.contrib.auth.models import User

        def test_access_to_setting():
            assert settings.SECRET_KEY == 'set from settings.configure()'

        # This test requires Django to be properly configured to be run
        def test_rf(rf):
            assert isinstance(rf, RequestFactory)

        # This tests that pytest-django actually configures the database
        # according to the settings above
        class ATestCase(TestCase):
            def test_user_count(self):
                assert User.objects.count() == 0

        @pytest.mark.django_db
        def test_user_count():
            assert User.objects.count() == 0

    """
    )
    result = pytester.runpython(p)
    result.stdout.fnmatch_lines(["* 4 passed*"])


def test_settings_in_hook(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")
    pytester.makeconftest(
        """
        from django.conf import settings

        def pytest_configure():
            settings.configure(SECRET_KEY='set from pytest_configure',
                               DATABASES={'default': {
                                   'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
                               INSTALLED_APPS=['django.contrib.auth',
                                               'django.contrib.contenttypes',])
    """
    )
    pytester.makepyfile(
        """
        import pytest
        from django.conf import settings
        from django.contrib.auth.models import User

        def test_access_to_setting():
            assert settings.SECRET_KEY == 'set from pytest_configure'

        @pytest.mark.django_db
        def test_user_count():
            assert User.objects.count() == 0
    """
    )
    r = pytester.runpytest_subprocess()
    assert r.ret == 0


def test_django_not_loaded_without_settings(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Make sure Django is not imported at all if no Django settings is specified.
    """
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")
    pytester.makepyfile(
        """
        import sys
        def test_settings():
            assert 'django' not in sys.modules
    """
    )
    result = pytester.runpytest_subprocess()
    result.stdout.fnmatch_lines(["* 1 passed*"])
    assert result.ret == 0


def test_debug_false_by_default(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")
    pytester.makeconftest(
        """
        from django.conf import settings

        def pytest_configure():
            settings.configure(SECRET_KEY='set from pytest_configure',
                               DEBUG=True,
                               DATABASES={'default': {
                                   'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
                               INSTALLED_APPS=['django.contrib.auth',
                                               'django.contrib.contenttypes',])
    """
    )

    pytester.makepyfile(
        """
        from django.conf import settings
        def test_debug_is_false():
            assert settings.DEBUG is False
    """
    )

    r = pytester.runpytest_subprocess()
    assert r.ret == 0


@pytest.mark.parametrize("django_debug_mode", [False, True])
def test_django_debug_mode_true_false(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
    django_debug_mode: bool,
) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")
    pytester.makeini(
        f"""
       [pytest]
       django_debug_mode = {django_debug_mode}
    """
    )
    pytester.makeconftest(
        """
        from django.conf import settings

        def pytest_configure():
            settings.configure(SECRET_KEY='set from pytest_configure',
                               DEBUG=%s,
                               DATABASES={'default': {
                                   'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
                               INSTALLED_APPS=['django.contrib.auth',
                                               'django.contrib.contenttypes',])
    """
        % (not django_debug_mode)
    )

    pytester.makepyfile(
        f"""
        from django.conf import settings
        def test_debug_is_false():
            assert settings.DEBUG is {django_debug_mode}
    """
    )

    r = pytester.runpytest_subprocess()
    assert r.ret == 0


@pytest.mark.parametrize("settings_debug", [False, True])
def test_django_debug_mode_keep(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
    settings_debug: bool,
) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")
    pytester.makeini(
        """
       [pytest]
       django_debug_mode = keep
    """
    )
    pytester.makeconftest(
        """
        from django.conf import settings

        def pytest_configure():
            settings.configure(SECRET_KEY='set from pytest_configure',
                               DEBUG=%s,
                               DATABASES={'default': {
                                   'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
                               INSTALLED_APPS=['django.contrib.auth',
                                               'django.contrib.contenttypes',])
    """
        % settings_debug
    )

    pytester.makepyfile(
        f"""
        from django.conf import settings
        def test_debug_is_false():
            assert settings.DEBUG is {settings_debug}
    """
    )

    r = pytester.runpytest_subprocess()
    assert r.ret == 0


@pytest.mark.django_project(
    extra_settings="""
    INSTALLED_APPS = [
        'tpkg.app.apps.TestApp',
    ]
"""
)
def test_django_setup_sequence(django_pytester) -> None:
    django_pytester.create_app_file(
        """
        from django.apps import apps, AppConfig


        class TestApp(AppConfig):
            name = 'tpkg.app'

            def ready(self):
                populating = apps.loading
                print('READY(): populating=%r' % populating)
        """,
        "apps.py",
    )

    django_pytester.create_app_file(
        """
        from django.apps import apps

        populating = apps.loading

        print('IMPORT: populating=%r,ready=%r' % (populating, apps.ready))
        SOME_THING = 1234
        """,
        "models.py",
    )

    django_pytester.create_app_file("", "__init__.py")
    django_pytester.makepyfile(
        """
        from django.apps import apps
        from tpkg.app.models import SOME_THING

        def test_anything():
            populating = apps.loading

            print('TEST: populating=%r,ready=%r' % (populating, apps.ready))
        """
    )

    result = django_pytester.runpytest_subprocess("-s", "--tb=line")
    result.stdout.fnmatch_lines(["*IMPORT: populating=True,ready=False*"])
    result.stdout.fnmatch_lines(["*READY(): populating=True*"])
    result.stdout.fnmatch_lines(["*TEST: populating=True,ready=True*"])
    assert result.ret == 0


def test_no_ds_but_django_imported(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """pytest-django should not bail out, if "django" has been imported
    somewhere, e.g. via pytest-splinter."""

    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")

    pytester.makepyfile(
        """
        import os
        import django

        from pytest_django.lazy_django import django_settings_is_configured

        def test_django_settings_is_configured():
            assert django_settings_is_configured() is False

        def test_env():
            assert 'DJANGO_SETTINGS_MODULE' not in os.environ

        def test_cfg(pytestconfig):
            assert pytestconfig.option.ds is None
    """
    )
    r = pytester.runpytest_subprocess("-s")
    assert r.ret == 0


def test_no_ds_but_django_conf_imported(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """pytest-django should not bail out, if "django.conf" has been imported
    somewhere, e.g. via hypothesis (#599)."""

    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")

    pytester.makepyfile(
        """
        import os
        import sys

        # line copied from hypothesis/extras/django.py
        from django.conf import settings as django_settings

        # Don't let pytest poke into this object, generating a
        # django.core.exceptions.ImproperlyConfigured
        del django_settings

        from pytest_django.lazy_django import django_settings_is_configured

        def test_django_settings_is_configured():
            assert django_settings_is_configured() is False

        def test_django_conf_is_imported():
            assert 'django.conf' in sys.modules

        def test_env():
            assert 'DJANGO_SETTINGS_MODULE' not in os.environ

        def test_cfg(pytestconfig):
            assert pytestconfig.option.ds is None
    """
    )
    r = pytester.runpytest_subprocess("-s")
    assert r.ret == 0


def test_no_django_settings_but_django_imported(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Make sure we do not crash when Django happens to be imported, but
    settings is not properly configured"""
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE")
    pytester.makeconftest("import django")
    r = pytester.runpytest_subprocess("--help")
    assert r.ret == 0
