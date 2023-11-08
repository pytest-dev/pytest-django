"""All pytest-django fixtures"""
from __future__ import annotations

import os
from contextlib import contextmanager
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    ContextManager,
    Generator,
    Iterable,
    List,
    Literal,
    Optional,
    Protocol,
    Tuple,
    Union,
)

import pytest

from . import live_server_helper
from .django_compat import is_django_unittest
from .lazy_django import skip_if_no_django


if TYPE_CHECKING:
    import django
    import django.test

    from . import DjangoDbBlocker


_DjangoDbDatabases = Optional[Union[Literal["__all__"], Iterable[str]]]
_DjangoDbAvailableApps = Optional[List[str]]
# transaction, reset_sequences, databases, serialized_rollback, available_apps
_DjangoDb = Tuple[bool, bool, _DjangoDbDatabases, bool, _DjangoDbAvailableApps]


__all__ = [
    "django_db_setup",
    "db",
    "transactional_db",
    "django_db_reset_sequences",
    "django_db_serialized_rollback",
    "admin_user",
    "django_user_model",
    "django_username_field",
    "client",
    "async_client",
    "admin_client",
    "rf",
    "async_rf",
    "settings",
    "live_server",
    "_live_server_helper",
    "django_assert_num_queries",
    "django_assert_max_num_queries",
    "django_capture_on_commit_callbacks",
]


@pytest.fixture(scope="session")
def django_db_modify_db_settings_tox_suffix() -> None:
    skip_if_no_django()

    tox_environment = os.getenv("TOX_PARALLEL_ENV")
    if tox_environment:
        # Put a suffix like _py27-django21 on tox workers
        _set_suffix_to_test_databases(suffix=tox_environment)


@pytest.fixture(scope="session")
def django_db_modify_db_settings_xdist_suffix(request: pytest.FixtureRequest) -> None:
    skip_if_no_django()

    xdist_suffix = getattr(request.config, "workerinput", {}).get("workerid")
    if xdist_suffix:
        # Put a suffix like _gw0, _gw1 etc on xdist processes
        _set_suffix_to_test_databases(suffix=xdist_suffix)


@pytest.fixture(scope="session")
def django_db_modify_db_settings_parallel_suffix(
    django_db_modify_db_settings_tox_suffix: None,
    django_db_modify_db_settings_xdist_suffix: None,
) -> None:
    skip_if_no_django()


@pytest.fixture(scope="session")
def django_db_modify_db_settings(
    django_db_modify_db_settings_parallel_suffix: None,
) -> None:
    skip_if_no_django()


@pytest.fixture(scope="session")
def django_db_use_migrations(request: pytest.FixtureRequest) -> bool:
    return not request.config.getvalue("nomigrations")


@pytest.fixture(scope="session")
def django_db_keepdb(request: pytest.FixtureRequest) -> bool:
    reuse_db: bool = request.config.getvalue("reuse_db")
    return reuse_db


@pytest.fixture(scope="session")
def django_db_createdb(request: pytest.FixtureRequest) -> bool:
    create_db: bool = request.config.getvalue("create_db")
    return create_db


@pytest.fixture(scope="session")
def django_db_setup(
    request: pytest.FixtureRequest,
    django_test_environment: None,
    django_db_blocker: DjangoDbBlocker,
    django_db_use_migrations: bool,
    django_db_keepdb: bool,
    django_db_createdb: bool,
    django_db_modify_db_settings: None,
) -> Generator[None, None, None]:
    """Top level fixture to ensure test databases are available"""
    from django.test.utils import setup_databases, teardown_databases

    setup_databases_args = {}

    if not django_db_use_migrations:
        _disable_migrations()

    if django_db_keepdb and not django_db_createdb:
        setup_databases_args["keepdb"] = True

    with django_db_blocker.unblock():
        db_cfg = setup_databases(
            verbosity=request.config.option.verbose,
            interactive=False,
            **setup_databases_args,
        )

    yield

    if not django_db_keepdb:
        with django_db_blocker.unblock():
            try:
                teardown_databases(db_cfg, verbosity=request.config.option.verbose)
            except Exception as exc:  # noqa: BLE001
                request.node.warn(
                    pytest.PytestWarning(f"Error when trying to teardown test databases: {exc!r}")
                )


@pytest.fixture()
def _django_db_helper(
    request: pytest.FixtureRequest,
    django_db_setup: None,
    django_db_blocker: DjangoDbBlocker,
) -> Generator[None, None, None]:
    from django import VERSION

    if is_django_unittest(request):
        yield
        return

    marker = request.node.get_closest_marker("django_db")
    if marker:
        (
            transactional,
            reset_sequences,
            databases,
            serialized_rollback,
            available_apps,
        ) = validate_django_db(marker)
    else:
        (
            transactional,
            reset_sequences,
            databases,
            serialized_rollback,
            available_apps,
        ) = False, False, None, False, None

    transactional = (
        transactional
        or reset_sequences
        or ("transactional_db" in request.fixturenames or "live_server" in request.fixturenames)
    )
    reset_sequences = reset_sequences or ("django_db_reset_sequences" in request.fixturenames)
    serialized_rollback = serialized_rollback or (
        "django_db_serialized_rollback" in request.fixturenames
    )

    django_db_blocker.unblock()

    import django.db
    import django.test

    if transactional:
        test_case_class = django.test.TransactionTestCase
    else:
        test_case_class = django.test.TestCase

    _reset_sequences = reset_sequences
    _serialized_rollback = serialized_rollback
    _databases = databases
    _available_apps = available_apps

    class PytestDjangoTestCase(test_case_class):  # type: ignore[misc,valid-type]
        reset_sequences = _reset_sequences
        serialized_rollback = _serialized_rollback
        if _databases is not None:
            databases = _databases
        if _available_apps is not None:
            available_apps = _available_apps

        # For non-transactional tests, skip executing `django.test.TestCase`'s
        # `setUpClass`/`tearDownClass`, only execute the super class ones.
        #
        # `TestCase`'s class setup manages the `setUpTestData`/class-level
        # transaction functionality. We don't use it; instead we (will) offer
        # our own alternatives. So it only adds overhead, and does some things
        # which conflict with our (planned) functionality, particularly, it
        # closes all database connections in `tearDownClass` which inhibits
        # wrapping tests in higher-scoped transactions.
        #
        # It's possible a new version of Django will add some unrelated
        # functionality to these methods, in which case skipping them completely
        # would not be desirable. Let's cross that bridge when we get there...
        if not transactional:

            @classmethod
            def setUpClass(cls) -> None:
                super(django.test.TestCase, cls).setUpClass()
                if VERSION < (4, 1):
                    django.db.transaction.Atomic._ensure_durability = False

            @classmethod
            def tearDownClass(cls) -> None:
                if VERSION < (4, 1):
                    django.db.transaction.Atomic._ensure_durability = True
                super(django.test.TestCase, cls).tearDownClass()

    PytestDjangoTestCase.setUpClass()

    test_case = PytestDjangoTestCase(methodName="__init__")
    test_case._pre_setup()

    yield

    test_case._post_teardown()

    PytestDjangoTestCase.tearDownClass()

    if VERSION >= (4, 0):
        PytestDjangoTestCase.doClassCleanups()

    django_db_blocker.restore()


def validate_django_db(marker) -> _DjangoDb:
    """Validate the django_db marker.

    It checks the signature and creates the ``transaction``,
    ``reset_sequences``, ``databases``, ``serialized_rollback`` and
    ``available_apps`` attributes on the marker which will have the correct
    values.

    Sequence reset, serialized_rollback, and available_apps are only allowed
    when combined with transaction.
    """

    def apifun(
        transaction: bool = False,
        reset_sequences: bool = False,
        databases: _DjangoDbDatabases = None,
        serialized_rollback: bool = False,
        available_apps: _DjangoDbAvailableApps = None,
    ) -> _DjangoDb:
        return transaction, reset_sequences, databases, serialized_rollback, available_apps

    return apifun(*marker.args, **marker.kwargs)


def _disable_migrations() -> None:
    from django.conf import settings
    from django.core.management.commands import migrate

    class DisableMigrations:
        def __contains__(self, item: str) -> bool:
            return True

        def __getitem__(self, item: str) -> None:
            return None

    settings.MIGRATION_MODULES = DisableMigrations()

    class MigrateSilentCommand(migrate.Command):
        def handle(self, *args, **kwargs):
            kwargs["verbosity"] = 0
            return super().handle(*args, **kwargs)

    migrate.Command = MigrateSilentCommand


def _set_suffix_to_test_databases(suffix: str) -> None:
    from django.conf import settings

    for db_settings in settings.DATABASES.values():
        test_name = db_settings.get("TEST", {}).get("NAME")

        if not test_name:
            if db_settings["ENGINE"] == "django.db.backends.sqlite3":
                continue
            test_name = f"test_{db_settings['NAME']}"

        if test_name == ":memory:":
            continue

        db_settings.setdefault("TEST", {})
        db_settings["TEST"]["NAME"] = f"{test_name}_{suffix}"


# ############### User visible fixtures ################


@pytest.fixture()
def db(_django_db_helper: None) -> None:
    """Require a django test database.

    This database will be setup with the default fixtures and will have
    the transaction management disabled. At the end of the test the outer
    transaction that wraps the test itself will be rolled back to undo any
    changes to the database (in case the backend supports transactions).
    This is more limited than the ``transactional_db`` fixture but
    faster.

    If both ``db`` and ``transactional_db`` are requested,
    ``transactional_db`` takes precedence.
    """
    # The `_django_db_helper` fixture checks if `db` is requested.


@pytest.fixture()
def transactional_db(_django_db_helper: None) -> None:
    """Require a django test database with transaction support.

    This will re-initialise the django database for each test and is
    thus slower than the normal ``db`` fixture.

    If you want to use the database with transactions you must request
    this resource.

    If both ``db`` and ``transactional_db`` are requested,
    ``transactional_db`` takes precedence.
    """
    # The `_django_db_helper` fixture checks if `transactional_db` is requested.


@pytest.fixture()
def django_db_reset_sequences(
    _django_db_helper: None,
    transactional_db: None,
) -> None:
    """Require a transactional test database with sequence reset support.

    This requests the ``transactional_db`` fixture, and additionally
    enforces a reset of all auto increment sequences.  If the enquiring
    test relies on such values (e.g. ids as primary keys), you should
    request this resource to ensure they are consistent across tests.
    """
    # The `_django_db_helper` fixture checks if `django_db_reset_sequences`
    # is requested.


@pytest.fixture()
def django_db_serialized_rollback(
    _django_db_helper: None,
    db: None,
) -> None:
    """Require a test database with serialized rollbacks.

    This requests the ``db`` fixture, and additionally performs rollback
    emulation - serializes the database contents during setup and restores
    it during teardown.

    This fixture may be useful for transactional tests, so is usually combined
    with ``transactional_db``, but can also be useful on databases which do not
    support transactions.

    Note that this will slow down that test suite by approximately 3x.
    """
    # The `_django_db_helper` fixture checks if `django_db_serialized_rollback`
    # is requested.


@pytest.fixture()
def client() -> django.test.Client:
    """A Django test client instance."""
    skip_if_no_django()

    from django.test import Client

    return Client()


@pytest.fixture()
def async_client() -> django.test.AsyncClient:
    """A Django test async client instance."""
    skip_if_no_django()

    from django.test import AsyncClient

    return AsyncClient()


@pytest.fixture()
def django_user_model(db: None):
    """The class of Django's user model."""
    from django.contrib.auth import get_user_model

    return get_user_model()


@pytest.fixture()
def django_username_field(django_user_model) -> str:
    """The fieldname for the username used with Django's user model."""
    field: str = django_user_model.USERNAME_FIELD
    return field


@pytest.fixture()
def admin_user(
    db: None,
    django_user_model,
    django_username_field: str,
):
    """A Django admin user.

    This uses an existing user with username "admin", or creates a new one with
    password "password".
    """
    UserModel = django_user_model
    username_field = django_username_field
    username = "admin@example.com" if username_field == "email" else "admin"

    try:
        # The default behavior of `get_by_natural_key()` is to look up by `username_field`.
        # However the user model is free to override it with any sort of custom behavior.
        # The Django authentication backend already assumes the lookup is by username,
        # so we can assume so as well.
        user = UserModel._default_manager.get_by_natural_key(username)
    except UserModel.DoesNotExist:
        user_data = {}
        if "email" in UserModel.REQUIRED_FIELDS:
            user_data["email"] = "admin@example.com"
        user_data["password"] = "password"
        user_data[username_field] = username
        user = UserModel._default_manager.create_superuser(**user_data)
    return user


@pytest.fixture()
def admin_client(
    db: None,
    admin_user,
) -> django.test.Client:
    """A Django test client logged in as an admin user."""
    from django.test import Client

    client = Client()
    client.force_login(admin_user)
    return client


@pytest.fixture()
def rf() -> django.test.RequestFactory:
    """RequestFactory instance"""
    skip_if_no_django()

    from django.test import RequestFactory

    return RequestFactory()


@pytest.fixture()
def async_rf() -> django.test.AsyncRequestFactory:
    """AsyncRequestFactory instance"""
    skip_if_no_django()

    from django.test import AsyncRequestFactory

    return AsyncRequestFactory()


class SettingsWrapper:
    _to_restore: ClassVar[list[Any]] = []

    def __delattr__(self, attr: str) -> None:
        from django.test import override_settings

        override = override_settings()
        override.enable()
        from django.conf import settings

        delattr(settings, attr)

        self._to_restore.append(override)

    def __setattr__(self, attr: str, value) -> None:
        from django.test import override_settings

        override = override_settings(**{attr: value})
        override.enable()
        self._to_restore.append(override)

    def __getattr__(self, attr: str):
        from django.conf import settings

        return getattr(settings, attr)

    def finalize(self) -> None:
        for override in reversed(self._to_restore):
            override.disable()

        del self._to_restore[:]


@pytest.fixture()
def settings():
    """A Django settings object which restores changes after the testrun"""
    skip_if_no_django()

    wrapper = SettingsWrapper()
    yield wrapper
    wrapper.finalize()


@pytest.fixture(scope="session")
def live_server(request: pytest.FixtureRequest):
    """Run a live Django server in the background during tests

    The address the server is started from is taken from the
    --liveserver command line option or if this is not provided from
    the DJANGO_LIVE_TEST_SERVER_ADDRESS environment variable.  If
    neither is provided ``localhost`` is used.  See the Django
    documentation for its full syntax.

    NOTE: If the live server needs database access to handle a request
          your test will have to request database access.  Furthermore
          when the tests want to see data added by the live-server (or
          the other way around) transactional database access will be
          needed as data inside a transaction is not shared between
          the live server and test code.

          Static assets will be automatically served when
          ``django.contrib.staticfiles`` is available in INSTALLED_APPS.
    """
    skip_if_no_django()

    addr = (
        request.config.getvalue("liveserver")
        or os.getenv("DJANGO_LIVE_TEST_SERVER_ADDRESS")
        or "localhost"
    )

    server = live_server_helper.LiveServer(addr)
    yield server
    server.stop()


@pytest.fixture(autouse=True)
def _live_server_helper(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Helper to make live_server work, internal to pytest-django.

    This helper will dynamically request the transactional_db fixture
    for a test which uses the live_server fixture.  This allows the
    server and test to access the database without having to mark
    this explicitly which is handy since it is usually required and
    matches the Django behaviour.

    The separate helper is required since live_server can not request
    transactional_db directly since it is session scoped instead of
    function-scoped.

    It will also override settings only for the duration of the test.
    """
    if "live_server" not in request.fixturenames:
        yield
        return

    request.getfixturevalue("transactional_db")

    live_server = request.getfixturevalue("live_server")
    live_server._live_server_modified_settings.enable()
    yield
    live_server._live_server_modified_settings.disable()


class DjangoAssertNumQueries(Protocol):
    """The type of the `django_assert_num_queries` and
    `django_assert_max_num_queries` fixtures."""

    def __call__(
        self,
        num: int,
        connection: Any | None = ...,
        info: str | None = ...,
    ) -> django.test.utils.CaptureQueriesContext:
        pass  # pragma: no cover


@contextmanager
def _assert_num_queries(
    config: pytest.Config,
    num: int,
    exact: bool = True,
    connection: Any | None = None,
    info: str | None = None,
) -> Generator[django.test.utils.CaptureQueriesContext, None, None]:
    from django.test.utils import CaptureQueriesContext

    if connection is None:
        from django.db import connection as conn
    else:
        conn = connection

    verbose = config.getoption("verbose") > 0
    with CaptureQueriesContext(conn) as context:
        yield context
        num_performed = len(context)
        if exact:
            failed = num != num_performed
        else:
            failed = num_performed > num
        if failed:
            msg = f"Expected to perform {num} queries "
            if not exact:
                msg += "or less "
            verb = "was" if num_performed == 1 else "were"
            msg += f"but {num_performed} {verb} done"
            if info:
                msg += f"\n{info}"
            if verbose:
                sqls = (q["sql"] for q in context.captured_queries)
                msg += "\n\nQueries:\n========\n\n" + "\n\n".join(sqls)
            else:
                msg += " (add -v option to show queries)"
            pytest.fail(msg)


@pytest.fixture()
def django_assert_num_queries(pytestconfig: pytest.Config) -> DjangoAssertNumQueries:
    return partial(_assert_num_queries, pytestconfig)


@pytest.fixture()
def django_assert_max_num_queries(pytestconfig: pytest.Config) -> DjangoAssertNumQueries:
    return partial(_assert_num_queries, pytestconfig, exact=False)


class DjangoCaptureOnCommitCallbacks(Protocol):
    """The type of the `django_capture_on_commit_callbacks` fixture."""

    def __call__(
        self,
        *,
        using: str = ...,
        execute: bool = ...,
    ) -> ContextManager[list[Callable[[], Any]]]:
        pass  # pragma: no cover


@pytest.fixture()
def django_capture_on_commit_callbacks() -> DjangoCaptureOnCommitCallbacks:
    from django.test import TestCase

    return TestCase.captureOnCommitCallbacks  # type: ignore[no-any-return]
