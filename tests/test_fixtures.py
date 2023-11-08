"""Tests for user-visible fixtures.

Not quite all fixtures are tested here, the db and transactional_db
fixtures are tested in test_database.
"""
import socket
from contextlib import contextmanager
from typing import Generator
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest
from django.conf import settings as real_settings
from django.core import mail
from django.db import connection, transaction
from django.test import AsyncClient, AsyncRequestFactory, Client, RequestFactory
from django.utils.encoding import force_str

from .helpers import DjangoPytester

from pytest_django import DjangoAssertNumQueries, DjangoCaptureOnCommitCallbacks, DjangoDbBlocker
from pytest_django_test.app.models import Item


@contextmanager
def nonverbose_config(config: pytest.Config) -> Generator[None, None, None]:
    """Ensure that pytest's config.option.verbose is <= 0."""
    if config.option.verbose <= 0:
        yield
    else:
        saved = config.option.verbose
        config.option.verbose = 0
        yield
        config.option.verbose = saved


def test_client(client: Client) -> None:
    assert isinstance(client, Client)


def test_async_client(async_client: AsyncClient) -> None:
    assert isinstance(async_client, AsyncClient)


@pytest.mark.django_db
def test_admin_client(admin_client: Client) -> None:
    assert isinstance(admin_client, Client)
    resp = admin_client.get("/admin-required/")
    assert force_str(resp.content) == "You are an admin"


def test_admin_client_no_db_marker(admin_client: Client) -> None:
    assert isinstance(admin_client, Client)
    resp = admin_client.get("/admin-required/")
    assert force_str(resp.content) == "You are an admin"


# For test below.
@pytest.fixture
def existing_admin_user(django_user_model):
    return django_user_model._default_manager.create_superuser("admin", None, None)


def test_admin_client_existing_user(
    db: None,
    existing_admin_user,
    admin_user,
    admin_client: Client,
) -> None:
    resp = admin_client.get("/admin-required/")
    assert force_str(resp.content) == "You are an admin"


@pytest.mark.django_db
def test_admin_user(admin_user, django_user_model) -> None:
    assert isinstance(admin_user, django_user_model)


def test_admin_user_no_db_marker(admin_user, django_user_model) -> None:
    assert isinstance(admin_user, django_user_model)


def test_rf(rf: RequestFactory) -> None:
    assert isinstance(rf, RequestFactory)


def test_async_rf(async_rf: AsyncRequestFactory) -> None:
    assert isinstance(async_rf, AsyncRequestFactory)


@pytest.mark.django_db
def test_django_assert_num_queries_db(
    request: pytest.FixtureRequest,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    with nonverbose_config(request.config):
        with django_assert_num_queries(3):
            Item.objects.create(name="foo")
            Item.objects.create(name="bar")
            Item.objects.create(name="baz")

        with pytest.raises(pytest.fail.Exception) as excinfo:
            with django_assert_num_queries(2) as captured:
                Item.objects.create(name="quux")
        assert excinfo.value.args == (
            "Expected to perform 2 queries but 1 was done " "(add -v option to show queries)",
        )
        assert len(captured.captured_queries) == 1


@pytest.mark.django_db
def test_django_assert_max_num_queries_db(
    request: pytest.FixtureRequest,
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    with nonverbose_config(request.config):
        with django_assert_max_num_queries(2):
            Item.objects.create(name="1-foo")
            Item.objects.create(name="2-bar")

        with pytest.raises(pytest.fail.Exception) as excinfo:  # noqa: PT012
            with django_assert_max_num_queries(2) as captured:
                Item.objects.create(name="1-foo")
                Item.objects.create(name="2-bar")
                Item.objects.create(name="3-quux")

        assert excinfo.value.args == (
            "Expected to perform 2 queries or less but 3 were done "
            "(add -v option to show queries)",
        )
        assert len(captured.captured_queries) == 3
        assert "1-foo" in captured.captured_queries[0]["sql"]


@pytest.mark.django_db(transaction=True)
def test_django_assert_num_queries_transactional_db(
    request: pytest.FixtureRequest,
    transactional_db: None,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    with nonverbose_config(request.config):
        with transaction.atomic():
            with django_assert_num_queries(3):
                Item.objects.create(name="foo")
                Item.objects.create(name="bar")
                Item.objects.create(name="baz")

            with pytest.raises(pytest.fail.Exception):
                with django_assert_num_queries(2):
                    Item.objects.create(name="quux")


def test_django_assert_num_queries_output(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        from django.contrib.contenttypes.models import ContentType
        import pytest

        @pytest.mark.django_db
        def test_queries(django_assert_num_queries):
            with django_assert_num_queries(1):
                list(ContentType.objects.all())
                ContentType.objects.count()
    """
    )
    result = django_pytester.runpytest_subprocess("--tb=short")
    result.stdout.fnmatch_lines(["*Expected to perform 1 queries but 2 were done*"])
    assert result.ret == 1


def test_django_assert_num_queries_output_verbose(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        from django.contrib.contenttypes.models import ContentType
        import pytest

        @pytest.mark.django_db
        def test_queries(django_assert_num_queries):
            with django_assert_num_queries(11):
                list(ContentType.objects.all())
                ContentType.objects.count()
    """
    )
    result = django_pytester.runpytest_subprocess("--tb=short", "-v")
    result.stdout.fnmatch_lines(
        ["*Expected to perform 11 queries but 2 were done*", "*Queries:*", "*========*"]
    )
    assert result.ret == 1


@pytest.mark.django_db
def test_django_assert_num_queries_db_connection(
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    from django.db import connection

    with django_assert_num_queries(1, connection=connection):
        Item.objects.create(name="foo")

    with django_assert_num_queries(1, connection=None):
        Item.objects.create(name="foo")

    with pytest.raises(AttributeError):
        with django_assert_num_queries(1, connection=False):
            pass


@pytest.mark.django_db
def test_django_assert_num_queries_output_info(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        from django.contrib.contenttypes.models import ContentType
        import pytest

        @pytest.mark.django_db
        def test_queries(django_assert_num_queries):
            with django_assert_num_queries(
                num=2,
                info="Expected: 1 for select all, 1 for count"
            ):
                list(ContentType.objects.all())
                ContentType.objects.count()
                ContentType.objects.first()  # additional wrong query
    """
    )
    result = django_pytester.runpytest_subprocess("--tb=short", "-v")
    result.stdout.fnmatch_lines(
        [
            "*Expected to perform 2 queries but 3 were done*",
            "*Expected: 1 for select all, 1 for count*",
            "*Queries:*",
            "*========*",
        ]
    )
    assert result.ret == 1


@pytest.mark.django_db
def test_django_capture_on_commit_callbacks(
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    if not connection.features.supports_transactions:
        pytest.skip("transactions required for this test")

    scratch = []
    with django_capture_on_commit_callbacks() as callbacks:
        transaction.on_commit(lambda: scratch.append("one"))
    assert len(callbacks) == 1
    assert scratch == []
    callbacks[0]()
    assert scratch == ["one"]

    scratch = []
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        transaction.on_commit(lambda: scratch.append("two"))
        transaction.on_commit(lambda: scratch.append("three"))
    assert len(callbacks) == 2
    assert scratch == ["two", "three"]
    callbacks[0]()
    assert scratch == ["two", "three", "two"]


@pytest.mark.django_db(databases=["default", "second"])
def test_django_capture_on_commit_callbacks_multidb(
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    if not connection.features.supports_transactions:
        pytest.skip("transactions required for this test")

    scratch = []
    with django_capture_on_commit_callbacks(using="default", execute=True) as callbacks:
        transaction.on_commit(lambda: scratch.append("one"))
    assert len(callbacks) == 1
    assert scratch == ["one"]

    scratch = []
    with django_capture_on_commit_callbacks(using="second", execute=True) as callbacks:
        transaction.on_commit(lambda: scratch.append("two"))  # pragma: no cover
    assert len(callbacks) == 0
    assert scratch == []

    scratch = []
    with django_capture_on_commit_callbacks(using="default", execute=True) as callbacks:
        transaction.on_commit(lambda: scratch.append("ten"))
        transaction.on_commit(lambda: scratch.append("twenty"), using="second")  # pragma: no cover
        transaction.on_commit(lambda: scratch.append("thirty"))
    assert len(callbacks) == 2
    assert scratch == ["ten", "thirty"]


@pytest.mark.django_db(transaction=True)
def test_django_capture_on_commit_callbacks_transactional(
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    if not connection.features.supports_transactions:
        pytest.skip("transactions required for this test")

    # Bad usage: no transaction (executes immediately).
    scratch = []
    with django_capture_on_commit_callbacks() as callbacks:
        transaction.on_commit(lambda: scratch.append("one"))
    assert len(callbacks) == 0
    assert scratch == ["one"]


class TestSettings:
    """Tests for the settings fixture, order matters"""

    def test_modify_existing(self, settings) -> None:
        assert settings.SECRET_KEY == "foobar"
        assert real_settings.SECRET_KEY == "foobar"
        settings.SECRET_KEY = "spam"
        assert settings.SECRET_KEY == "spam"
        assert real_settings.SECRET_KEY == "spam"

    def test_modify_existing_again(self, settings) -> None:
        assert settings.SECRET_KEY == "foobar"
        assert real_settings.SECRET_KEY == "foobar"

    def test_new(self, settings) -> None:
        assert not hasattr(settings, "SPAM")
        assert not hasattr(real_settings, "SPAM")
        settings.SPAM = "ham"
        assert settings.SPAM == "ham"
        assert real_settings.SPAM == "ham"

    def test_new_again(self, settings) -> None:
        assert not hasattr(settings, "SPAM")
        assert not hasattr(real_settings, "SPAM")

    def test_deleted(self, settings) -> None:
        assert hasattr(settings, "SECRET_KEY")
        assert hasattr(real_settings, "SECRET_KEY")
        del settings.SECRET_KEY
        assert not hasattr(settings, "SECRET_KEY")
        assert not hasattr(real_settings, "SECRET_KEY")

    def test_deleted_again(self, settings) -> None:
        assert hasattr(settings, "SECRET_KEY")
        assert hasattr(real_settings, "SECRET_KEY")

    def test_signals(self, settings) -> None:
        result = []

        def assert_signal(signal, sender, setting, value, enter) -> None:
            result.append((setting, value, enter))

        from django.test.signals import setting_changed

        setting_changed.connect(assert_signal)

        result = []
        settings.SECRET_KEY = "change 1"
        settings.SECRET_KEY = "change 2"
        assert result == [
            ("SECRET_KEY", "change 1", True),
            ("SECRET_KEY", "change 2", True),
        ]

        result = []
        settings.FOOBAR = "abc123"
        assert sorted(result) == [("FOOBAR", "abc123", True)]

    def test_modification_signal(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
            import pytest

            from django.conf import settings
            from django.test.signals import setting_changed


            @pytest.fixture(autouse=True, scope='session')
            def settings_change_printer():
                def receiver(sender, **kwargs):
                    fmt_dict = {'actual_value': getattr(settings, kwargs['setting'],
                                                        '<<does not exist>>')}
                    fmt_dict.update(kwargs)

                    print('Setting changed: '
                          'enter=%(enter)s,setting=%(setting)s,'
                          'value=%(value)s,actual_value=%(actual_value)s'
                          % fmt_dict)

                setting_changed.connect(receiver, weak=False)


            def test_set(settings):
                settings.SECRET_KEY = 'change 1'
                settings.SECRET_KEY = 'change 2'


            def test_set_non_existent(settings):
                settings.FOOBAR = 'abc123'
         """
        )

        result = django_pytester.runpytest_subprocess("--tb=short", "-v", "-s")

        # test_set
        result.stdout.fnmatch_lines(
            [
                "*Setting changed: enter=True,setting=SECRET_KEY,value=change 1*",
                "*Setting changed: enter=True,setting=SECRET_KEY,value=change 2*",
                "*Setting changed: enter=False,setting=SECRET_KEY,value=change 1*",
                "*Setting changed: enter=False,setting=SECRET_KEY,value=foobar*",
            ]
        )

        result.stdout.fnmatch_lines(
            [
                "*Setting changed: enter=True,setting=FOOBAR,value=abc123*",
                (
                    "*Setting changed: enter=False,setting=FOOBAR,value=None,"
                    "actual_value=<<does not exist>>*"
                ),
            ]
        )


class TestLiveServer:
    def test_settings_before(self) -> None:
        from django.conf import settings

        assert (
            f"{settings.__class__.__module__}.{settings.__class__.__name__}"
            == "django.conf.Settings"
        )
        TestLiveServer._test_settings_before_run = True  # type: ignore[attr-defined]

    def test_url(self, live_server) -> None:
        assert live_server.url == force_str(live_server)

    def test_change_settings(self, live_server, settings) -> None:
        assert live_server.url == force_str(live_server)

    def test_settings_restored(self) -> None:
        """Ensure that settings are restored after test_settings_before."""
        from django.conf import settings

        assert TestLiveServer._test_settings_before_run is True  # type: ignore[attr-defined]
        assert (
            f"{settings.__class__.__module__}.{settings.__class__.__name__}"
            == "django.conf.Settings"
        )
        assert settings.ALLOWED_HOSTS == ["testserver"]

    def test_transactions(self, live_server) -> None:
        if not connection.features.supports_transactions:
            pytest.skip("transactions required for this test")

        assert not connection.in_atomic_block

    def test_db_changes_visibility(self, live_server) -> None:
        response_data = urlopen(live_server + "/item_count/").read()
        assert force_str(response_data) == "Item count: 0"
        Item.objects.create(name="foo")
        response_data = urlopen(live_server + "/item_count/").read()
        assert force_str(response_data) == "Item count: 1"

    def test_fixture_db(self, db: None, live_server) -> None:
        Item.objects.create(name="foo")
        response_data = urlopen(live_server + "/item_count/").read()
        assert force_str(response_data) == "Item count: 1"

    def test_fixture_transactional_db(self, transactional_db: None, live_server) -> None:
        Item.objects.create(name="foo")
        response_data = urlopen(live_server + "/item_count/").read()
        assert force_str(response_data) == "Item count: 1"

    @pytest.fixture
    def item(self) -> Item:
        # This has not requested database access explicitly, but the
        # live_server fixture auto-uses the transactional_db fixture.
        item: Item = Item.objects.create(name="foo")
        return item

    def test_item(self, item: Item, live_server) -> None:
        pass

    @pytest.fixture
    def item_db(self, db: None) -> Item:
        item: Item = Item.objects.create(name="foo")
        return item

    def test_item_db(self, item_db: Item, live_server) -> None:
        response_data = urlopen(live_server + "/item_count/").read()
        assert force_str(response_data) == "Item count: 1"

    @pytest.fixture
    def item_transactional_db(self, transactional_db: None) -> Item:
        item: Item = Item.objects.create(name="foo")
        return item

    def test_item_transactional_db(self, item_transactional_db: Item, live_server) -> None:
        response_data = urlopen(live_server + "/item_count/").read()
        assert force_str(response_data) == "Item count: 1"

    @pytest.mark.django_project(
        extra_settings="""
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'tpkg.app',
        ]

        STATIC_URL = '/static/'
        """
    )
    def test_serve_static_with_staticfiles_app(
        self,
        django_pytester: DjangoPytester,
        settings,
    ) -> None:
        """
        LiveServer always serves statics with ``django.contrib.staticfiles``
        handler.
        """
        django_pytester.create_test_module(
            """
            from urllib.request import urlopen

            from django.utils.encoding import force_str

            class TestLiveServer:
                def test_a(self, live_server, settings):
                    assert ('django.contrib.staticfiles'
                            in settings.INSTALLED_APPS)
                    response_data = urlopen(
                        live_server + '/static/a_file.txt').read()
                    assert force_str(response_data) == 'bla\\n'
            """
        )
        result = django_pytester.runpytest_subprocess("--tb=short", "-v")
        result.stdout.fnmatch_lines(["*test_a*PASSED*"])
        assert result.ret == 0

    def test_serve_static_dj17_without_staticfiles_app(self, live_server, settings) -> None:
        """
        Because ``django.contrib.staticfiles`` is not installed
        LiveServer can not serve statics with django >= 1.7 .
        """
        with pytest.raises(HTTPError):
            urlopen(live_server + "/static/a_file.txt").read()

    def test_specified_port_django_111(self, django_pytester: DjangoPytester) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("", 0))
            __, port = sock.getsockname()
        finally:
            sock.close()

        django_pytester.create_test_module(
            """
        def test_with_live_server(live_server):
            assert live_server.port == %d
        """
            % port
        )

        django_pytester.runpytest_subprocess(f"--liveserver=localhost:{port}")


@pytest.mark.parametrize("username_field", ["email", "identifier"])
@pytest.mark.django_project(
    extra_settings="""
    AUTH_USER_MODEL = 'app.MyCustomUser'
    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'tpkg.app',
    ]
    ROOT_URLCONF = 'tpkg.app.urls'
    """
)
def test_custom_user_model(django_pytester: DjangoPytester, username_field: str) -> None:
    django_pytester.create_app_file(
        f"""
        from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
        from django.db import models

        class MyCustomUserManager(BaseUserManager):
            def create_user(self, {username_field}, password=None, **extra_fields):
                extra_fields.setdefault('is_staff', False)
                extra_fields.setdefault('is_superuser', False)
                user = self.model({username_field}={username_field}, **extra_fields)
                user.set_password(password)
                user.save()
                return user

            def create_superuser(self, {username_field}, password=None, **extra_fields):
                extra_fields.setdefault('is_staff', True)
                extra_fields.setdefault('is_superuser', True)
                return self.create_user(
                    {username_field}={username_field},
                    password=password,
                    **extra_fields
                )

        class MyCustomUser(AbstractBaseUser, PermissionsMixin):
            email = models.EmailField(max_length=100, unique=True)
            identifier = models.CharField(unique=True, max_length=100)
            is_staff = models.BooleanField(
                'staff status',
                default=False,
                help_text='Designates whether the user can log into this admin site.'
            )

            objects = MyCustomUserManager()

            USERNAME_FIELD = '{username_field}'
        """,
        "models.py",
    )
    django_pytester.create_app_file(
        """
        from django.urls import path

        from tpkg.app import views

        urlpatterns = [path('admin-required/', views.admin_required_view)]
        """,
        "urls.py",
    )
    django_pytester.create_app_file(
        """
        from django.http import HttpResponse
        from django.template import Template
        from django.template.context import Context


        def admin_required_view(request):
            assert request.user.is_staff
            return HttpResponse(Template('You are an admin').render(Context()))
        """,
        "views.py",
    )
    django_pytester.makepyfile(
        """
        from django.utils.encoding import force_str
        from tpkg.app.models import MyCustomUser

        def test_custom_user_model(admin_client):
            resp = admin_client.get('/admin-required/')
            assert force_str(resp.content) == 'You are an admin'
        """
    )

    django_pytester.create_app_file("", "migrations/__init__.py")
    django_pytester.create_app_file(
        """
from django.db import models, migrations
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyCustomUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(error_messages={'unique': 'A user with that email address already exists.'}, max_length=100, unique=True, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('identifier', models.CharField(unique=True, max_length=100)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=None,
        ),
    ]
        """,
        "migrations/0002_custom_user_model.py",
    )

    result = django_pytester.runpytest_subprocess("-s")
    result.stdout.fnmatch_lines(["* 1 passed*"])
    assert result.ret == 0


class Test_django_db_blocker:
    @pytest.mark.django_db
    def test_block_manually(self, django_db_blocker: DjangoDbBlocker) -> None:
        try:
            django_db_blocker.block()
            with pytest.raises(RuntimeError):
                Item.objects.exists()
        finally:
            django_db_blocker.restore()

    @pytest.mark.django_db
    def test_block_with_block(self, django_db_blocker: DjangoDbBlocker) -> None:
        with django_db_blocker.block():
            with pytest.raises(RuntimeError):
                Item.objects.exists()

    def test_unblock_manually(self, django_db_blocker: DjangoDbBlocker) -> None:
        try:
            django_db_blocker.unblock()
            Item.objects.exists()
        finally:
            django_db_blocker.restore()

    def test_unblock_with_block(self, django_db_blocker: DjangoDbBlocker) -> None:
        with django_db_blocker.unblock():
            Item.objects.exists()


def test_mail(mailoutbox) -> None:
    assert mailoutbox is mail.outbox  # check that mail.outbox and fixture value is same object
    assert len(mailoutbox) == 0
    mail.send_mail("subject", "body", "from@example.com", ["to@example.com"])
    assert len(mailoutbox) == 1
    m = mailoutbox[0]
    assert m.subject == "subject"
    assert m.body == "body"
    assert m.from_email == "from@example.com"
    assert list(m.to) == ["to@example.com"]


def test_mail_again(mailoutbox) -> None:
    test_mail(mailoutbox)


def test_mail_message_uses_mocked_DNS_NAME(mailoutbox) -> None:
    mail.send_mail("subject", "body", "from@example.com", ["to@example.com"])
    m = mailoutbox[0]
    message = m.message()
    assert message["Message-ID"].endswith("@fake-tests.example.com>")


def test_mail_message_uses_django_mail_dnsname_fixture(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        from django.core import mail
        import pytest

        @pytest.fixture
        def django_mail_dnsname():
            return 'from.django_mail_dnsname'

        def test_mailbox_inner(mailoutbox):
            mail.send_mail('subject', 'body', 'from@example.com',
                           ['to@example.com'])
            m = mailoutbox[0]
            message = m.message()
            assert message['Message-ID'].endswith('@from.django_mail_dnsname>')
    """
    )
    result = django_pytester.runpytest_subprocess("--tb=short", "-v")
    result.stdout.fnmatch_lines(["*test_mailbox_inner*PASSED*"])
    assert result.ret == 0


def test_mail_message_dns_patching_can_be_skipped(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        from django.core import mail
        import pytest

        @pytest.fixture
        def django_mail_dnsname():
            raise Exception('should not get called')

        @pytest.fixture
        def django_mail_patch_dns():
            print('\\ndjango_mail_dnsname_mark')

        def test_mailbox_inner(mailoutbox, monkeypatch):
            def mocked_make_msgid(*args, **kwargs):
                mocked_make_msgid.called += [(args, kwargs)]
            mocked_make_msgid.called = []

            monkeypatch.setattr(mail.message, 'make_msgid', mocked_make_msgid)
            mail.send_mail('subject', 'body', 'from@example.com',
                           ['to@example.com'])
            m = mailoutbox[0]
            assert len(mocked_make_msgid.called) == 1

            assert mocked_make_msgid.called[0][1]['domain'] is mail.DNS_NAME
    """
    )
    result = django_pytester.runpytest_subprocess("--tb=short", "-vv", "-s")
    result.stdout.fnmatch_lines(["*test_mailbox_inner*", "django_mail_dnsname_mark", "PASSED*"])
    assert result.ret == 0
