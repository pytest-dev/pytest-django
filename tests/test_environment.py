from __future__ import with_statement

import os

import pytest
from django.core import mail
from django.db import connection

from pytest_django_test.app.models import Item


# It doesn't matter which order all the _again methods are run, we just need
# to check the environment remains constant.
# This is possible with some of the testdir magic, but this is the lazy way
# to do it.


def test_mail():
    assert len(mail.outbox) == 0
    mail.send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
    assert len(mail.outbox) == 1
    m = mail.outbox[0]
    assert m.subject == 'subject'
    assert m.body == 'body'
    assert m.from_email == 'from@example.com'
    assert list(m.to) == ['to@example.com']


def test_mail_again():
    test_mail()


@pytest.mark.django_project(extra_settings="""
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )
    ROOT_URLCONF = 'tpkg.app.urls'
    """)
def test_invalid_template_variable(django_testdir):
    django_testdir.create_app_file("""
        from django.conf.urls import url
        from pytest_django_test.compat import patterns

        from tpkg.app import views

        urlpatterns = patterns(
            '',
            url(r'invalid_template/', views.invalid_template),
        )
        """, 'urls.py')
    django_testdir.create_app_file("""
        from django.shortcuts import render


        def invalid_template(request):
            return render(request, 'invalid_template.html', {})
        """, 'views.py')
    django_testdir.create_app_file(
        "<div>{{ invalid_var }}</div>",
        'templates/invalid_template.html'
    )
    django_testdir.create_test_module('''
        import pytest

        def test_for_invalid_template(client):
            client.get('/invalid_template/')

        @pytest.mark.ignore_template_errors
        def test_ignore(client):
            client.get('/invalid_template/')
        ''')
    result = django_testdir.runpytest_subprocess('-s', '--fail-on-template-vars')
    result.stdout.fnmatch_lines_random([
        "tpkg/test_the_test.py F.",
        "Undefined template variable 'invalid_var' in 'invalid_template.html'",
    ])


@pytest.mark.django_project(extra_settings="""
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )
    ROOT_URLCONF = 'tpkg.app.urls'
    """)
def test_invalid_template_variable_opt_in(django_testdir):
    django_testdir.create_app_file("""
        from django.conf.urls import url
        from pytest_django_test.compat import patterns

        from tpkg.app import views

        urlpatterns = patterns(
            '',
            url(r'invalid_template/', views.invalid_template),
        )
        """, 'urls.py')
    django_testdir.create_app_file("""
        from django.shortcuts import render


        def invalid_template(request):
            return render(request, 'invalid_template.html', {})
        """, 'views.py')
    django_testdir.create_app_file(
        "<div>{{ invalid_var }}</div>",
        'templates/invalid_template.html'
    )
    django_testdir.create_test_module('''
        import pytest

        def test_for_invalid_template(client):
            client.get('/invalid_template/')

        @pytest.mark.ignore_template_errors
        def test_ignore(client):
            client.get('/invalid_template/')
        ''')
    result = django_testdir.runpytest_subprocess('-s')
    result.stdout.fnmatch_lines_random([
        "tpkg/test_the_test.py ..",
    ])


@pytest.mark.django_db
def test_database_rollback():
    assert Item.objects.count() == 0
    Item.objects.create(name='blah')
    assert Item.objects.count() == 1


@pytest.mark.django_db
def test_database_rollback_again():
    test_database_rollback()


@pytest.mark.django_db
def test_database_name():
    dirname, name = os.path.split(connection.settings_dict['NAME'])
    assert 'file:memorydb' in name or name == ':memory:' or name.startswith('test_')


def test_database_noaccess():
    with pytest.raises(pytest.fail.Exception):
        Item.objects.count()


class TestrunnerVerbosity:
    """Test that Django's code to setup and teardown the databases uses
    pytest's verbosity level."""

    @pytest.fixture
    def testdir(self, django_testdir):
        print("testdir")
        django_testdir.create_test_module('''
            import pytest

            @pytest.mark.django_db
            def test_inner_testrunner():
                pass
            ''')
        return django_testdir

    def test_default(self, testdir):
        """Not verbose by default."""
        result = testdir.runpytest_subprocess('-s')
        result.stdout.fnmatch_lines([
            "tpkg/test_the_test.py ."])

    def test_vq_verbosity_0(self, testdir):
        """-v and -q results in verbosity 0."""
        result = testdir.runpytest_subprocess('-s', '-v', '-q')
        result.stdout.fnmatch_lines([
            "tpkg/test_the_test.py ."])

    def test_verbose_with_v(self, testdir):
        """Verbose output with '-v'."""
        result = testdir.runpytest_subprocess('-s', '-v')
        result.stdout.fnmatch_lines_random([
            "tpkg/test_the_test.py:*",
            "*PASSED*",
            "*Destroying test database for alias 'default'...*"])

    def test_more_verbose_with_vv(self, testdir):
        """More verbose output with '-v -v'."""
        result = testdir.runpytest_subprocess('-s', '-v', '-v')
        result.stdout.fnmatch_lines([
            "tpkg/test_the_test.py:*Creating test database for alias*",
            '*Operations to perform:*',
            "*Apply all migrations:*",
            "*PASSED*Destroying test database for alias 'default' ('*')...*"])

    def test_more_verbose_with_vv_and_reusedb(self, testdir):
        """More verbose output with '-v -v', and --create-db."""
        result = testdir.runpytest_subprocess('-s', '-v', '-v', '--create-db')
        result.stdout.fnmatch_lines([
            "tpkg/test_the_test.py:*Creating test database for alias*",
            "*PASSED*"])
        assert ("*Destroying test database for alias 'default' ('*')...*"
                not in result.stdout.str())
