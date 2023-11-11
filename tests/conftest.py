from __future__ import annotations

import copy
import os
import pathlib
import shutil
from pathlib import Path
from textwrap import dedent
from typing import cast

import pytest
from django.conf import settings

from .helpers import DjangoPytester


pytest_plugins = "pytester"

REPOSITORY_ROOT = pathlib.Path(__file__).parent.parent


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "django_project: options for the django_pytester fixture",
    )


def _marker_apifun(
    extra_settings: str = "",
    create_manage_py: bool = False,
    project_root: str | None = None,
):
    return {
        "extra_settings": extra_settings,
        "create_manage_py": create_manage_py,
        "project_root": project_root,
    }


@pytest.fixture
def pytester(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> pytest.Pytester:
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    return pytester


@pytest.fixture()
def django_pytester(
    request: pytest.FixtureRequest,
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> DjangoPytester:
    from pytest_django_test.db_helpers import (
        DB_NAME,
        SECOND_DB_NAME,
        SECOND_TEST_DB_NAME,
        TEST_DB_NAME,
    )

    marker = request.node.get_closest_marker("django_project")

    options = _marker_apifun(**(marker.kwargs if marker else {}))

    if hasattr(request.node.cls, "db_settings"):
        db_settings = request.node.cls.db_settings
    else:
        db_settings = copy.deepcopy(settings.DATABASES)
        db_settings["default"]["NAME"] = DB_NAME
        db_settings["default"]["TEST"]["NAME"] = TEST_DB_NAME
        db_settings["second"]["NAME"] = SECOND_DB_NAME
        db_settings["second"].setdefault("TEST", {})["NAME"] = SECOND_TEST_DB_NAME

    test_settings = dedent(
        """
        import django

        # Pypy compatibility
        try:
            from psycopg2cffi import compat
        except ImportError:
            pass
        else:
            compat.register()

        DATABASES = %(db_settings)s
        DATABASE_ROUTERS = ['pytest_django_test.db_router.DbRouter']

        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'tpkg.app',
        ]
        SECRET_KEY = 'foobar'

        MIDDLEWARE = [
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ]

        TEMPLATES = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {},
            },
        ]

        %(extra_settings)s
        """
    ) % {
        "db_settings": repr(db_settings),
        "extra_settings": dedent(options["extra_settings"]),
    }

    if options["project_root"]:
        project_root = pytester.mkdir(options["project_root"])
    else:
        project_root = pytester.path

    tpkg_path = project_root / "tpkg"
    tpkg_path.mkdir()

    if options["create_manage_py"]:
        project_root.joinpath("manage.py").touch()

    tpkg_path.joinpath("__init__.py").touch()

    app_source = REPOSITORY_ROOT / "pytest_django_test/app"
    test_app_path = tpkg_path / "app"

    # Copy the test app to make it available in the new test run
    shutil.copytree(str(app_source), str(test_app_path))
    tpkg_path.joinpath("the_settings.py").write_text(test_settings)

    # For suprocess tests, pytest's `pythonpath` setting doesn't currently
    # work, only the envvar does.
    pythonpath = os.pathsep.join(filter(None, [str(REPOSITORY_ROOT), os.getenv("PYTHONPATH", "")]))
    monkeypatch.setenv("PYTHONPATH", pythonpath)

    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tpkg.the_settings")

    def create_test_module(test_code: str, filename: str = "test_the_test.py") -> Path:
        r = tpkg_path.joinpath(filename)
        r.parent.mkdir(parents=True, exist_ok=True)
        r.write_text(dedent(test_code))
        return r

    def create_app_file(code: str, filename: str) -> Path:
        r = test_app_path.joinpath(filename)
        r.parent.mkdir(parents=True, exist_ok=True)
        r.write_text(dedent(code))
        return r

    pytester.makeini(
        """
        [pytest]
        addopts = --strict-markers
        console_output_style=classic
    """
    )

    django_pytester_ = cast(DjangoPytester, pytester)
    django_pytester_.create_test_module = create_test_module  # type: ignore[method-assign]
    django_pytester_.create_app_file = create_app_file  # type: ignore[method-assign]
    django_pytester_.project_root = project_root

    return django_pytester_


@pytest.fixture
def django_pytester_initial(django_pytester: DjangoPytester) -> pytest.Pytester:
    """A django_pytester fixture which provides initial_data."""
    shutil.rmtree(django_pytester.project_root.joinpath("tpkg/app/migrations"))
    django_pytester.makefile(
        ".json",
        initial_data="""
        [{
            "pk": 1,
            "model": "app.item",
            "fields": { "name": "mark_initial_data" }
        }]""",
    )

    return django_pytester
