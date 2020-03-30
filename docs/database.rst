Database creation/re-use
========================

``pytest-django`` takes a conservative approach to enabling database
access.  By default your tests will fail if they try to access the
database.  Only if you explicitly request database access will this be
allowed.  This encourages you to keep database-needing tests to a
minimum which is a best practice since next-to-no business logic
should be requiring the database.  Moreover it makes it very clear
what code uses the database and catches any mistakes.

Enabling database access in tests
---------------------------------

You can use `pytest marks <https://pytest.org/en/latest/mark.html>`_ to
tell ``pytest-django`` your test needs database access::

   import pytest

   @pytest.mark.django_db
   def test_my_user():
       me = User.objects.get(username='me')
       assert me.is_superuser

It is also possible to mark all tests in a class or module at once.
This demonstrates all the ways of marking, even though they overlap.
Just one of these marks would have been sufficient.  See the `pytest
documentation
<https://pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules>`_
for detail::

   import pytest

   pytestmark = pytest.mark.django_db

   @pytest.mark.django_db
   class TestUsers:
       pytestmark = pytest.mark.django_db
       def test_my_user(self):
           me = User.objects.get(username='me')
           assert me.is_superuser


By default ``pytest-django`` will set up the Django databases the
first time a test needs them.  Once setup the database is cached for
used for all subsequent tests and rolls back transactions to isolate
tests from each other.  This is the same way the standard Django
`TestCase
<https://docs.djangoproject.com/en/1.9/topics/testing/tools/#testcase>`_
uses the database.  However ``pytest-django`` also caters for
transaction test cases and allows you to keep the test databases
configured across different test runs.


Testing transactions
--------------------

Django itself has the ``TransactionTestCase`` which allows you to test
transactions and will flush the database between tests to isolate
them.  The downside of this is that these tests are much slower to
set up due to the required flushing of the database.
``pytest-django`` also supports this style of tests, which you can
select using an argument to the ``django_db`` mark::

   @pytest.mark.django_db(transaction=True)
   def test_spam():
       pass  # test relying on transactions


Tests requiring multiple databases
----------------------------------

Currently ``pytest-django`` does not specifically support Django's
multi-database support.

You can however use normal :class:`~django.test.TestCase` instances to use its
:ref:`django:topics-testing-advanced-multidb` support.
In particular, if your database is configured for replication, be sure to read
about :ref:`django:topics-testing-primaryreplica`.

If you have any ideas about the best API to support multiple databases
directly in ``pytest-django`` please get in touch, we are interested
in eventually supporting this but unsure about simply following
Django's approach.

See `https://github.com/pytest-dev/pytest-django/pull/431` for an idea /
discussion to approach this.

``--reuse-db`` - reuse the testing database between test runs
--------------------------------------------------------------
Using ``--reuse-db`` will create the test database in the same way as
``manage.py test`` usually does.

However, after the test run, the test database will not be removed.

The next time a test run is started with ``--reuse-db``, the database will
instantly be re used. This will allow much faster startup time for tests.

This can be especially useful when running a few tests, when there are a lot
of database tables to set up.

``--reuse-db`` will not pick up schema changes between test runs. You must run
the tests with ``--reuse-db --create-db`` to re-create the database according
to the new schema. Running without ``--reuse-db`` is also possible, since the
database will automatically be re-created.


``--create-db`` - force re creation of the test database
--------------------------------------------------------
When used with ``--reuse-db``, this option will re-create the database,
regardless of whether it exists or not.

Example work flow with ``--reuse-db`` and ``--create-db``.
-----------------------------------------------------------
A good way to use ``--reuse-db`` and ``--create-db`` can be:

* Put ``--reuse-db`` in your default options (in your project's ``pytest.ini`` file)::

    [pytest]
    addopts = --reuse-db

* Just run tests with ``pytest``, on the first run the test database will be
  created. The next test run it will be reused.

* When you alter your database schema, run ``pytest --create-db``, to force
  re-creation of the test database.

``--nomigrations`` - Disable Django migrations
----------------------------------------------

Using ``--nomigrations`` will disable Django migrations and create the database
by inspecting all models. It may be faster when there are several migrations to
run in the database setup.  You can use ``--migrations`` to force running
migrations in case ``--nomigrations`` is used, e.g. in ``setup.cfg``.

.. _advanced-database-configuration:

Advanced database configuration
-------------------------------

pytest-django provides options to customize the way database is configured. The
default database construction mostly follows Django's own test runner. You can
however influence all parts of the database setup process to make it fit in
projects with special requirements.

This section assumes some familiarity with the Django test runner, Django
database creation and pytest fixtures.

Fixtures
########

There are some fixtures which will let you change the way the database is
configured in your own project. These fixtures can be overridden in your own
project by specifying a fixture with the same name and scope in ``conftest.py``.

.. admonition:: Use the pytest-django source code

    The default implementation of these fixtures can be found in
    `fixtures.py <https://github.com/pytest-dev/pytest-django/blob/master/pytest_django/fixtures.py>`_.

    The code is relatively short and straightforward and can provide a
    starting point when you need to customize database setup in your own
    project.


django_db_setup
"""""""""""""""

.. fixture:: django_db_setup

This is the top-level fixture that ensures that the test databases are created
and available. This fixture is session scoped (it will be run once per test
session) and is responsible for making sure the test database is available for tests
that need it.

The default implementation creates the test database by applying migrations and removes
databases after the test run.

You can override this fixture in your own ``conftest.py`` to customize how test
databases are constructed.

django_db_modify_db_settings
""""""""""""""""""""""""""""

.. fixture:: django_db_modify_db_settings

This fixture allows modifying `django.conf.settings.DATABASES` just before the
databases are configured.

If you need to customize the location of your test database, this is the
fixture you want to override.

The default implementation of this fixture requests the
:fixture:`django_db_modify_db_settings_parallel_suffix` to provide compatibility
with pytest-xdist.

This fixture is by default requested from :fixture:`django_db_setup`.

django_db_modify_db_settings_parallel_suffix
""""""""""""""""""""""""""""""""""""""""""""

.. fixture:: django_db_modify_db_settings_parallel_suffix

Requesting this fixture will add a suffix to the database name when the tests
are run via `pytest-xdist`, or via `tox` in parallel mode.

This fixture is by default requested from
:fixture:`django_db_modify_db_settings`.

django_db_modify_db_settings_tox_suffix
"""""""""""""""""""""""""""""""""""""""

.. fixture:: django_db_modify_db_settings_tox_suffix

Requesting this fixture will add a suffix to the database name when the tests
are run via `tox` in parallel mode.

This fixture is by default requested from
:fixture:`django_db_modify_db_settings_parallel_suffix`.

django_db_modify_db_settings_xdist_suffix
"""""""""""""""""""""""""""""""""""""""""

.. fixture:: django_db_modify_db_settings_xdist_suffix

Requesting this fixture will add a suffix to the database name when the tests
are run via `pytest-xdist`.

This fixture is by default requested from
:fixture:`django_db_modify_db_settings_parallel_suffix`.

django_db_use_migrations
""""""""""""""""""""""""

.. fixture:: django_db_use_migrations

Returns whether or not to use migrations to create the test
databases.

The default implementation returns the value of the
``--migrations``/``--nomigrations`` command line options.

This fixture is by default requested from :fixture:`django_db_setup`.

django_db_keepdb
""""""""""""""""

.. fixture:: django_db_keepdb

Returns whether or not to re-use an existing database and to keep it after the
test run.

The default implementation handles the ``--reuse-db`` and ``--create-db``
command line options.

This fixture is by default requested from :fixture:`django_db_setup`.

django_db_createdb
""""""""""""""""""

.. fixture:: django_db_createdb

Returns whether or not the database is to be re-created before running any
tests.

This fixture is by default requested from :fixture:`django_db_setup`.

django_db_blocker
"""""""""""""""""

.. fixture:: django_db_blocker

.. warning::
    It does not manage transactions and changes made to the database will not
    be automatically restored. Using the ``pytest.mark.django_db`` marker
    or :fixture:`db` fixture, which wraps database changes in a transaction and
    restores the state is generally the thing you want in tests. This marker
    can be used when you are trying to influence the way the database is
    configured.

Database access is by default not allowed. ``django_db_blocker`` is the object
which can allow specific code paths to have access to the database. This
fixture is used internally to implement the ``db`` fixture.


:fixture:`django_db_blocker` can be used as a context manager to enable database
access for the specified block::

    @pytest.fixture
    def myfixture(django_db_blocker):
        with django_db_blocker.unblock():
            ...  # modify something in the database

You can also manage the access manually via these methods:

.. py:method:: django_db_blocker.unblock()

  Enable database access. Should be followed by a call to
  :func:`~django_db_blocker.restore`.

.. py:method:: django_db_blocker.block()

  Disable database access. Should be followed by a call to
  :func:`~django_db_blocker.restore`.

.. py:function:: django_db_blocker.restore()

  Restore the previous state of the database blocking.

Examples
########

Using a template database for tests
"""""""""""""""""""""""""""""""""""

This example shows how a pre-created PostgreSQL source database can be copied
and used for tests.

Put this into ``conftest.py``::

    import pytest
    from django.db import connections

    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


    def run_sql(sql):
        conn = psycopg2.connect(database='postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(sql)
        conn.close()


    @pytest.yield_fixture(scope='session')
    def django_db_setup():
        from django.conf import settings

        settings.DATABASES['default']['NAME'] = 'the_copied_db'

        run_sql('DROP DATABASE IF EXISTS the_copied_db')
        run_sql('CREATE DATABASE the_copied_db TEMPLATE the_source_db')

        yield

        for connection in connections.all():
            connection.close()

        run_sql('DROP DATABASE the_copied_db')


Using an existing, external database for tests
""""""""""""""""""""""""""""""""""""""""""""""

This example shows how you can connect to an existing database and use it for
your tests. This example is trivial, you just need to disable all of
pytest-django and Django's test database creation and point to the existing
database. This is achieved by simply implementing a no-op
:fixture:`django_db_setup` fixture.

Put this into ``conftest.py``::

    import pytest


    @pytest.fixture(scope='session')
    def django_db_setup():
        settings.DATABASES['default'] = {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': 'db.example.com',
            'NAME': 'external_db',
        }


Populate the database with initial test data
""""""""""""""""""""""""""""""""""""""""""""

This example shows how you can populate the test database with test data. The
test data will be saved in the database, i.e. it will not just be part of a
transactions. This example uses Django's fixture loading mechanism, but it can
be replaced with any way of loading data into the database.

Notice that :fixture:`django_db_setup` is in the argument list. This may look
odd at first, but it will make sure that the original pytest-django fixture
is used to create the test database. When ``call_command`` is invoked, the
test database is already prepared and configured.

Put this in ``conftest.py``::

    import pytest

    from django.core.management import call_command

    @pytest.fixture(scope='session')
    def django_db_setup(django_db_setup, django_db_blocker):
        with django_db_blocker.unblock():
            call_command('loaddata', 'your_data_fixture.json')

Use the same database for all xdist processes
"""""""""""""""""""""""""""""""""""""""""""""

By default, each xdist process gets its own database to run tests on. This is
needed to have transactional tests that do not interfere with each other.

If you instead want your tests to use the same database, override the
:fixture:`django_db_modify_db_settings` to not do anything. Put this in
``conftest.py``::

    import pytest


    @pytest.fixture(scope='session')
    def django_db_modify_db_settings():
        pass

Randomize database sequences
""""""""""""""""""""""""""""

You can customize the test database after it has been created by extending the
:fixture:`django_db_setup` fixture. This example shows how to give a PostgreSQL
sequence a random starting value. This can be used to detect and prevent
primary key id's from being hard-coded in tests.

Put this in ``conftest.py``::

    import random
    import pytest
    from django.db import connection


    @pytest.fixture(scope='session')
    def django_db_setup(django_db_setup, django_db_blocker):
        with django_db_blocker.unblock():
            cur = connection.cursor()
            cur.execute('ALTER SEQUENCE app_model_id_seq RESTART WITH %s;',
                        [random.randint(10000, 20000)])

Create the test database from a custom SQL script
"""""""""""""""""""""""""""""""""""""""""""""""""

You can replace the :fixture:`django_db_setup` fixture and run any code in its
place. This includes creating your database by hand by running a SQL script
directly. This example shows sqlite3's executescript method. In a more
general use case, you probably want to load the SQL statements from a file or
invoke the ``psql`` or the ``mysql`` command line tool.

Put this in ``conftest.py``::

    import pytest
    from django.db import connection


    @pytest.fixture(scope='session')
    def django_db_setup(django_db_blocker):
        with django_db_blocker.unblock():
            with connection.cursor() as c:
                c.executescript('''
                DROP TABLE IF EXISTS theapp_item;
                CREATE TABLE theapp_item (id, name);
                INSERT INTO theapp_item (name) VALUES ('created from a sql script');
                ''')

.. warning::
    This snippet shows ``cursor().executescript()`` which is `sqlite` specific, for
    other database engines this method might differ. For instance, psycopg2 uses
    ``cursor().execute()``.


Use a read only database
""""""""""""""""""""""""

You can replace the ordinary `django_db_setup` to completely avoid database
creation/migrations. If you have no need for rollbacks or truncating tables,
you can simply avoid blocking the database and use it directly. When using this
method you must ensure that your tests do not change the database state.


Put this in ``conftest.py``::

    import pytest


    @pytest.fixture(scope='session')
    def django_db_setup():
        """Avoid creating/setting up the test database"""
        pass


    @pytest.fixture
    def db_access_without_rollback_and_truncate(request, django_db_setup, django_db_blocker):
        django_db_blocker.unblock()
        request.addfinalizer(django_db_blocker.restore)
