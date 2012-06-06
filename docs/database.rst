Database creation/re-use
========================

By default, when invoking ``py.test`` with ``pytest-django`` installed,
databases defined in the settings will be created the same way as when
``manage.py test`` is invoked.

``pytest-django`` offers some greater flexibility how the test database
should be created/destroyed.


``--no-db`` - disable database access
--------------------------------------
This option can be given to prevent the database from being accessed during
test runs. It will raise exceptions for any Django database access. It can be
useful when writing pure unit tests to make sure database access does not
happens by accident.


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
regardless of wheter it exists or not. This option will be ignored unless
``--no-db`` is also given.


Example work flow with ``--reuse-db`` and ``--create-db``.
-----------------------------------------------------------
A good way to use ``--reuse-db`` and ``--create-db`` can be:

* Put ``--reuse-db`` in your default options (in your project's ``pytest.ini`` file)::

    [pytest]
    addopts = --reuse-db

* Just run tests with ``py.test``, on the first run the test database will be
  created. The next test run it will be reused.

* When you alter your database schema, run ``py.test --create-db``, to force
  re-creation of the test database.
