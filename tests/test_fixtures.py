"""Tests for user-visible fixtures.

Not quite all fixtures are tested here, the db and transactional_db
fixtures are tested in test_database.
"""

from __future__ import with_statement

import pytest
from django.conf import settings as real_settings
from django.test.client import Client, RequestFactory
from django.test.testcases import connections_support_transactions

from pytest_django.lazy_django import get_django_version
from pytest_django_test.app.models import Item
from pytest_django_test.compat import force_text, HTTPError, urlopen
from pytest_django_test.db_helpers import noop_transactions


def test_client(client):
    assert isinstance(client, Client)


@pytest.mark.django_db
def test_admin_client(admin_client):
    assert isinstance(admin_client, Client)
    resp = admin_client.get('/admin-required/')
    assert force_text(resp.content) == 'You are an admin'


def test_admin_client_no_db_marker(admin_client):
    assert isinstance(admin_client, Client)
    resp = admin_client.get('/admin-required/')
    assert force_text(resp.content) == 'You are an admin'


@pytest.mark.django_db
def test_admin_user(admin_user, django_user_model):
    assert isinstance(admin_user, django_user_model)


def test_admin_user_no_db_marker(admin_user, django_user_model):
    assert isinstance(admin_user, django_user_model)


def test_rf(rf):
    assert isinstance(rf, RequestFactory)


class TestSettings:
    """Tests for the settings fixture, order matters"""

    def test_modify_existing(self, settings):
        assert settings.SECRET_KEY == 'foobar'
        assert real_settings.SECRET_KEY == 'foobar'
        settings.SECRET_KEY = 'spam'
        assert settings.SECRET_KEY == 'spam'
        assert real_settings.SECRET_KEY == 'spam'

    def test_modify_existing_again(self, settings):
        assert settings.SECRET_KEY == 'foobar'
        assert real_settings.SECRET_KEY == 'foobar'

    def test_new(self, settings):
        assert not hasattr(settings, 'SPAM')
        assert not hasattr(real_settings, 'SPAM')
        settings.SPAM = 'ham'
        assert settings.SPAM == 'ham'
        assert real_settings.SPAM == 'ham'

    def test_new_again(self, settings):
        assert not hasattr(settings, 'SPAM')
        assert not hasattr(real_settings, 'SPAM')

    def test_deleted(self, settings):
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(real_settings, 'SECRET_KEY')
        del settings.SECRET_KEY
        assert not hasattr(settings, 'SECRET_KEY')
        assert not hasattr(real_settings, 'SECRET_KEY')

    def test_deleted_again(self, settings):
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(real_settings, 'SECRET_KEY')


class TestLiveServer:
    pytestmark = [
        pytest.mark.skipif(get_django_version() < (1, 4),
                           reason="Django > 1.3 required"),
    ]

    def test_url(self, live_server):
        assert live_server.url == force_text(live_server)

    def test_transactions(self, live_server):
        if not connections_support_transactions():
            pytest.skip('transactions required for this test')

        assert not noop_transactions()

    def test_db_changes_visibility(self, live_server):
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 0'
        Item.objects.create(name='foo')
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 1'

    def test_fixture_db(self, db, live_server):
        Item.objects.create(name='foo')
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 1'

    def test_fixture_transactional_db(self, transactional_db, live_server):
        Item.objects.create(name='foo')
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 1'

    @pytest.fixture
    def item(self):
        # This has not requested database access so should fail.
        # Unfortunately the _live_server_helper autouse fixture makes this
        # test work.
        with pytest.raises(pytest.fail.Exception):
            Item.objects.create(name='foo')

    @pytest.mark.xfail
    def test_item(self, item, live_server):
        # test should fail/pass in setup
        pass

    @pytest.fixture
    def item_db(self, db):
        return Item.objects.create(name='foo')

    def test_item_db(self, item_db, live_server):
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 1'

    @pytest.fixture
    def item_transactional_db(self, transactional_db):
        return Item.objects.create(name='foo')

    def test_item_transactional_db(self, item_transactional_db, live_server):
        response_data = urlopen(live_server + '/item_count/').read()
        assert force_text(response_data) == 'Item count: 1'

    @pytest.mark.skipif(get_django_version() >= (1, 7),
                        reason="Django < 1.7 required")
    def test_serve_static(self, live_server, settings):
        """
        Test that the LiveServer serves static files by default.
        """
        response_data = urlopen(live_server + '/static/a_file.txt').read()
        assert force_text(response_data) == 'bla\n'

    @pytest.mark.django_project(extra_settings="""
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'tpkg.app',
        ]

        STATIC_URL = '/static/'
        """)
    def test_serve_static_with_staticfiles_app(self, django_testdir, settings):
        """
        LiveServer always serves statics with ``django.contrib.staticfiles``
        handler.
        """
        django_testdir.create_test_module("""
            import pytest
            try:
                from django.utils.encoding import force_text
            except ImportError:
                from django.utils.encoding import force_unicode as force_text

            try:
                from urllib2 import urlopen, HTTPError
            except ImportError:
                from urllib.request import urlopen, HTTPError

            class TestLiveServer:
                def test_a(self, live_server, settings):
                    assert ('django.contrib.staticfiles'
                            in settings.INSTALLED_APPS)
                    response_data = urlopen(
                        live_server + '/static/a_file.txt').read()
                    assert force_text(response_data) == 'bla\\n'
            """)
        result = django_testdir.runpytest('--tb=short', '-v')
        result.stdout.fnmatch_lines(['*test_a*PASSED*'])

    @pytest.mark.skipif(get_django_version() < (1, 7),
                        reason="Django >= 1.7 required")
    def test_serve_static_dj17_without_staticfiles_app(self, live_server,
                                                       settings):
        """
        Because ``django.contrib.staticfiles`` is not installed
        LiveServer can not serve statics with django >= 1.7 .
        """
        with pytest.raises(HTTPError):
            urlopen(live_server + '/static/a_file.txt').read()


@pytest.mark.django_project(extra_settings="""
    AUTH_USER_MODEL = 'app.MyCustomUser'
    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'tpkg.app',
    ]
    ROOT_URLCONF = 'tpkg.app.urls'
    """)
@pytest.mark.skipif(get_django_version() < (1, 5),
                    reason="Django >= 1.5 required")
def test_custom_user_model(django_testdir):
    django_testdir.create_app_file("""
        from django.contrib.auth.models import AbstractUser
        from django.db import models

        class MyCustomUser(AbstractUser):
            identifier = models.CharField(unique=True, max_length=100)

            USERNAME_FIELD = 'identifier'
        """, 'models.py')
    django_testdir.create_app_file("""
        try:
            from django.conf.urls import patterns  # Django >1.4
        except ImportError:
            from django.conf.urls.defaults import patterns  # Django 1.3

        urlpatterns = patterns(
            '',
            (r'admin-required/', 'tpkg.app.views.admin_required_view'),
        )
        """, 'urls.py')
    django_testdir.create_app_file("""
        from django.http import HttpResponse
        from django.template import Template
        from django.template.context import Context


        def admin_required_view(request):
            if request.user.is_staff:
                return HttpResponse(
                    Template('You are an admin').render(Context()))
            return HttpResponse(
                    Template('Access denied').render(Context()))
        """, 'views.py')
    django_testdir.makepyfile("""
        from pytest_django_test.compat import force_text
        from tpkg.app.models import MyCustomUser

        def test_custom_user_model(admin_client):
            resp = admin_client.get('/admin-required/')
            assert force_text(resp.content) == 'You are an admin'
        """)

    django_testdir.create_app_file('', 'migrations/__init__.py')
    django_testdir.create_app_file("""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0005_alter_user_last_login_null'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyCustomUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=30, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, verbose_name='username')),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(max_length=254, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('identifier', models.CharField(unique=True, max_length=100)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=None,
        ),
    ]
    """, 'migrations/0001_initial.py')  # noqa

    result = django_testdir.runpytest('-s')
    result.stdout.fnmatch_lines(['*1 passed*'])
