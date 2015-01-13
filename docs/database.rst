Database creation/re-use
========================

``pytest-django`` takes a conservative approach to enabling database
access.  By default your tests will fail if they try to access the
database.  Only if you explicitly request database access will this be
allowed.  This encourages you to keep database-needing tests to a
minimum which is a best practice since next-to-no business logic
should be requiring the database.  Moreover it makes it very clear
what code uses the database and catches any mistakes.

Enabling database access
------------------------

You can use `py.test marks <http://pytest.org/latest/mark.html>`_ to
tell ``pytest-django`` your test needs database access::

   import pytest

   @pytest.mark.django_db
   def test_my_user():
       me = User.objects.get(username='me')
       assert me.is_superuser

It is also possible to mark all tests in a class or module at once.
This demonstrates all the ways of marking, even though they overlap.
Just one of these marks would have been sufficient.  See the `py.test
documentation
<http://pytest.org/latest/example/markers.html#marking-whole-classes-or-modules>`_
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
<https://docs.djangoproject.com/en/1.4/topics/testing/#testcase>`_
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
multi-database support.  You can however use normal Django
``TestCase`` instances to use it's `multi_db
<https://docs.djangoproject.com/en/1.4/topics/testing/#multi-database-support>`_
support.

If you have any ideas about the best API to support multiple databases
directly in ``pytest-django`` please get in touch, we are interested
in eventually supporting this but unsure about simply following
Django's approach.


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

* Just run tests with ``py.test``, on the first run the test database will be
  created. The next test run it will be reused.

* When you alter your database schema, run ``py.test --create-db``, to force
  re-creation of the test database.

``--nomigrations`` - Disable Django 1.7+ migrations
--------------------------------------------------------------

Using ``--nomigrations`` will `disable Django 1.7+ migrations <https://gist.github.com/NotSqrt/5f3c76cd15e40ef62d09>`_
and create the database inspecting all app models (the default behavior of
Django until version 1.6). It may be faster when there are several migrations
to run in the database setup.
