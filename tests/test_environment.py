import os

import pytest
from django.contrib.sites import models as site_models
from django.contrib.sites.models import Site
from django.core import mail
from django.db import connection
from django.test import TestCase

from .helpers import DjangoPytester

from pytest_django_test.app.models import Item


# It doesn't matter which order all the _again methods are run, we just need
# to check the environment remains constant.
# This is possible with some of the pytester magic, but this is the lazy way
# to do it.


@pytest.mark.parametrize("subject", ["subject1", "subject2"])
def test_autoclear_mailbox(subject: str) -> None:
    assert len(mail.outbox) == 0
    mail.send_mail(subject, "body", "from@example.com", ["to@example.com"])
    assert len(mail.outbox) == 1

    m = mail.outbox[0]
    assert m.subject == subject
    assert m.body == "body"
    assert m.from_email == "from@example.com"
    assert m.to == ["to@example.com"]


class TestDirectAccessWorksForDjangoTestCase(TestCase):
    def _do_test(self) -> None:
        assert len(mail.outbox) == 0
        mail.send_mail("subject", "body", "from@example.com", ["to@example.com"])
        assert len(mail.outbox) == 1

    def test_one(self) -> None:
        self._do_test()

    def test_two(self) -> None:
        self._do_test()


@pytest.mark.django_project(
    extra_settings="""
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )
    ROOT_URLCONF = 'tpkg.app.urls'
    """
)
def test_invalid_template_variable(django_pytester: DjangoPytester) -> None:
    django_pytester.create_app_file(
        """
        from django.urls import path

        from tpkg.app import views

        urlpatterns = [path('invalid_template/', views.invalid_template)]
        """,
        "urls.py",
    )
    django_pytester.create_app_file(
        """
        from django.shortcuts import render


        def invalid_template(request):
            return render(request, 'invalid_template.html', {})
        """,
        "views.py",
    )
    django_pytester.create_app_file(
        "<div>{{ invalid_var }}</div>", "templates/invalid_template_base.html"
    )
    django_pytester.create_app_file(
        "{% include 'invalid_template_base.html' %}", "templates/invalid_template.html"
    )
    django_pytester.create_test_module(
        """
        import pytest

        def test_for_invalid_template(client):
            client.get('/invalid_template/')

        @pytest.mark.ignore_template_errors
        def test_ignore(client):
            client.get('/invalid_template/')
        """
    )
    result = django_pytester.runpytest_subprocess("-s", "--fail-on-template-vars")

    origin = "'*/tpkg/app/templates/invalid_template_base.html'"
    result.stdout.fnmatch_lines_random(
        [
            "tpkg/test_the_test.py F.*",
            f"E * Failed: Undefined template variable 'invalid_var' in {origin}",
        ]
    )


@pytest.mark.django_project(
    extra_settings="""
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )
    """
)
def test_invalid_template_variable_marker_cleanup(django_pytester: DjangoPytester) -> None:
    django_pytester.create_app_file(
        "<div>{{ invalid_var }}</div>", "templates/invalid_template_base.html"
    )
    django_pytester.create_app_file(
        "{% include 'invalid_template_base.html' %}", "templates/invalid_template.html"
    )
    django_pytester.create_test_module(
        """
        from django.template.loader import render_to_string

        import pytest

        @pytest.mark.ignore_template_errors
        def test_ignore(client):
            render_to_string('invalid_template.html')

        def test_for_invalid_template(client):
            render_to_string('invalid_template.html')

        """
    )
    result = django_pytester.runpytest_subprocess("-s", "--fail-on-template-vars")

    origin = "'*/tpkg/app/templates/invalid_template_base.html'"
    result.stdout.fnmatch_lines_random(
        [
            "tpkg/test_the_test.py .F*",
            f"E * Failed: Undefined template variable 'invalid_var' in {origin}",
        ]
    )


@pytest.mark.django_project(
    extra_settings="""
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )
    ROOT_URLCONF = 'tpkg.app.urls'
    """
)
def test_invalid_template_with_default_if_none(django_pytester: DjangoPytester) -> None:
    django_pytester.create_app_file(
        """
            <div>{{ data.empty|default:'d' }}</div>
            <div>{{ data.none|default:'d' }}</div>
            <div>{{ data.empty|default_if_none:'d' }}</div>
            <div>{{ data.none|default_if_none:'d' }}</div>
            <div>{{ data.missing|default_if_none:'d' }}</div>
        """,
        "templates/the_template.html",
    )
    django_pytester.create_test_module(
        """
        def test_for_invalid_template():
            from django.shortcuts import render


            render(
                request=None,
                template_name='the_template.html',
                context={'data': {'empty': '', 'none': None}},
            )
        """
    )
    result = django_pytester.runpytest_subprocess("--fail-on-template-vars")
    result.stdout.fnmatch_lines(
        [
            "tpkg/test_the_test.py F",
            "E * Failed: Undefined template variable 'data.missing' in *the_template.html'",
        ]
    )


@pytest.mark.django_project(
    extra_settings="""
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )
    ROOT_URLCONF = 'tpkg.app.urls'
    """
)
def test_invalid_template_variable_opt_in(django_pytester: DjangoPytester) -> None:
    django_pytester.create_app_file(
        """
        from django.urls import path

        from tpkg.app import views

        urlpatterns = [path('invalid_template', views.invalid_template)]
        """,
        "urls.py",
    )
    django_pytester.create_app_file(
        """
        from django.shortcuts import render


        def invalid_template(request):
            return render(request, 'invalid_template.html', {})
        """,
        "views.py",
    )
    django_pytester.create_app_file(
        "<div>{{ invalid_var }}</div>", "templates/invalid_template.html"
    )
    django_pytester.create_test_module(
        """
        import pytest

        def test_for_invalid_template(client):
            client.get('/invalid_template/')

        @pytest.mark.ignore_template_errors
        def test_ignore(client):
            client.get('/invalid_template/')
        """
    )
    result = django_pytester.runpytest_subprocess("-s")
    result.stdout.fnmatch_lines_random(["tpkg/test_the_test.py ..*"])


@pytest.mark.django_db
def test_database_rollback() -> None:
    assert Item.objects.count() == 0
    Item.objects.create(name="blah")
    assert Item.objects.count() == 1


@pytest.mark.django_db
def test_database_rollback_again() -> None:
    test_database_rollback()


@pytest.mark.django_db
def test_database_name() -> None:
    dirname, name = os.path.split(connection.settings_dict["NAME"])
    assert "file:memorydb" in name or name == ":memory:" or name.startswith("test_")


def test_database_noaccess() -> None:
    with pytest.raises(RuntimeError):
        Item.objects.count()


class TestrunnerVerbosity:
    """Test that Django's code to setup and teardown the databases uses
    pytest's verbosity level."""

    @pytest.fixture
    def pytester(self, django_pytester: DjangoPytester) -> pytest.Pytester:
        print("pytester")
        django_pytester.create_test_module(
            """
            import pytest

            @pytest.mark.django_db
            def test_inner_testrunner():
                pass
            """
        )
        return django_pytester

    def test_default(self, pytester: pytest.Pytester) -> None:
        """Not verbose by default."""
        result = pytester.runpytest_subprocess("-s")
        result.stdout.fnmatch_lines(["tpkg/test_the_test.py .*"])

    def test_vq_verbosity_0(self, pytester: pytest.Pytester) -> None:
        """-v and -q results in verbosity 0."""
        result = pytester.runpytest_subprocess("-s", "-v", "-q")
        result.stdout.fnmatch_lines(["tpkg/test_the_test.py .*"])

    def test_verbose_with_v(self, pytester: pytest.Pytester) -> None:
        """Verbose output with '-v'."""
        result = pytester.runpytest_subprocess("-s", "-v")
        result.stdout.fnmatch_lines_random(["tpkg/test_the_test.py:*", "*PASSED*"])
        result.stderr.fnmatch_lines(["*Destroying test database for alias 'default'*"])

    def test_more_verbose_with_vv(self, pytester: pytest.Pytester) -> None:
        """More verbose output with '-v -v'."""
        result = pytester.runpytest_subprocess("-s", "-v", "-v")
        result.stdout.fnmatch_lines_random(
            [
                "tpkg/test_the_test.py:*",
                "*Operations to perform:*",
                "*Apply all migrations:*",
                "*PASSED*",
            ]
        )
        result.stderr.fnmatch_lines(
            [
                "*Creating test database for alias*",
                "*Destroying test database for alias 'default'*",
            ]
        )

    def test_more_verbose_with_vv_and_reusedb(self, pytester: pytest.Pytester) -> None:
        """More verbose output with '-v -v', and --create-db."""
        result = pytester.runpytest_subprocess("-s", "-v", "-v", "--create-db")
        result.stdout.fnmatch_lines(["tpkg/test_the_test.py:*", "*PASSED*"])
        result.stderr.fnmatch_lines(["*Creating test database for alias*"])
        assert "*Destroying test database for alias 'default' ('*')...*" not in result.stderr.str()


@pytest.mark.django_db
@pytest.mark.parametrize("site_name", ["site1", "site2"])
def test_clear_site_cache(site_name: str, rf, monkeypatch: pytest.MonkeyPatch) -> None:
    request = rf.get("/")
    monkeypatch.setattr(request, "get_host", lambda: "foo.com")
    Site.objects.create(domain="foo.com", name=site_name)
    assert Site.objects.get_current(request=request).name == site_name


@pytest.mark.django_db
@pytest.mark.parametrize("site_name", ["site1", "site2"])
def test_clear_site_cache_check_site_cache_size(site_name: str, settings) -> None:
    assert len(site_models.SITE_CACHE) == 0
    site = Site.objects.create(domain="foo.com", name=site_name)
    settings.SITE_ID = site.id
    assert Site.objects.get_current() == site
    assert len(site_models.SITE_CACHE) == 1
