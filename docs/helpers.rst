.. _helpers:

Django helpers
==============

Assertions
----------

All of Django's :py:class:`~django:django.test.TestCase`
:ref:`django:assertions` are available in ``pytest_django.asserts``, e.g.

::

    from pytest_django.asserts import assertTemplateUsed

Markers
-------

``pytest-django`` registers and uses markers.  See the pytest
:ref:`documentation <pytest:mark>` on what marks are and for notes on
:ref:`using <pytest:scoped-marking>` them.


``pytest.mark.django_db`` - request database access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: pytest.mark.django_db([transaction=False, reset_sequences=False])

  This is used to mark a test function as requiring the database. It
  will ensure the database is set up correctly for the test. Each test
  will run in its own transaction which will be rolled back at the end
  of the test. This behavior is the same as Django's standard
  :class:`~django.test.TestCase` class.

  In order for a test to have access to the database it must either be marked
  using the :func:`~pytest.mark.django_db` mark or request one of the :fixture:`db`,
  :fixture:`transactional_db` or :fixture:`django_db_reset_sequences` fixtures.
  Otherwise the test will fail when trying to access the database.

  :type transaction: bool
  :param transaction:
    The ``transaction`` argument will allow the test to use real transactions.
    With ``transaction=False`` (the default when not specified), transaction
    operations are noops during the test. This is the same behavior that
    :class:`django.test.TestCase` uses. When ``transaction=True``, the behavior
    will be the same as :class:`django.test.TransactionTestCase`.


  :type reset_sequences: bool
  :param reset_sequences:
    The ``reset_sequences`` argument will ask to reset auto increment sequence
    values (e.g. primary keys) before running the test.  Defaults to
    ``False``.  Must be used together with ``transaction=True`` to have an
    effect.  Please be aware that not all databases support this feature.
    For details see :py:attr:`django.test.TransactionTestCase.reset_sequences`.

.. note::

  If you want access to the Django database inside a *fixture*, this marker may
  or may not help even if the function requesting your fixture has this marker
  applied, depending on pytest's fixture execution order. To access the
  database in a fixture, it is recommended that the fixture explicitly request
  one of the :fixture:`db`, :fixture:`transactional_db` or
  :fixture:`django_db_reset_sequences` fixtures. See below for a description of
  them.

.. note:: Automatic usage with ``django.test.TestCase``.

 Test classes that subclass :class:`django.test.TestCase` will have access to
 the database always to make them compatible with existing Django tests.
 Test classes that subclass Python's :class:`unittest.TestCase` need to have
 the marker applied in order to access the database.


``pytest.mark.urls`` - override the urlconf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: pytest.mark.urls(urls)

   Specify a different ``settings.ROOT_URLCONF`` module for the marked tests.

   :type urls: str
   :param urls:
     The urlconf module to use for the test, e.g. ``myapp.test_urls``.  This is
     similar to Django's ``TestCase.urls`` attribute.

   Example usage::

     @pytest.mark.urls('myapp.test_urls')
     def test_something(client):
         assert 'Success!' in client.get('/some_url_defined_in_test_urls/').content


``pytest.mark.ignore_template_errors`` - ignore invalid template variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: pytest.mark.ignore_template_errors

  Ignore errors when using the ``--fail-on-template-vars`` option, i.e.
  do not cause tests to fail if your templates contain invalid variables.

  This marker sets the ``string_if_invalid`` template option.
  See :ref:`django:invalid-template-variables`.

  Example usage::

     @pytest.mark.ignore_template_errors
     def test_something(client):
         client('some-url-with-invalid-template-vars')


Fixtures
--------

pytest-django provides some pytest fixtures to provide dependencies for tests.
More information on fixtures is available in the :ref:`pytest documentation
<pytest:fixtures>`.

.. fixture:: rf

``rf`` - ``RequestFactory``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a :class:`django.test.RequestFactory`.

Example
"""""""

::

    from myapp.views import my_view

    def test_details(rf):
        request = rf.get('/customer/details')
        response = my_view(request)
        assert response.status_code == 200

.. fixture:: async_rf

``async_rf`` - ``AsyncRequestFactory``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a `django.test.AsyncRequestFactory`_.

.. _django.test.AsyncRequestFactory: https://docs.djangoproject.com/en/stable/topics/testing/advanced/#asyncrequestfactory

Example
"""""""

This example uses `pytest-asyncio <https://github.com/pytest-dev/pytest-asyncio>`_.

::

    from myapp.views import my_view

    @pytest.mark.asyncio
    async def test_details(async_rf):
        request = await async_rf.get('/customer/details')
        response = my_view(request)
        assert response.status_code == 200

.. fixture:: client

``client`` - ``django.test.Client``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a :class:`django.test.Client`.

Example
"""""""

::

    def test_with_client(client):
        response = client.get('/')
        assert response.content == 'Foobar'

To use `client` as an authenticated standard user, call its
:meth:`force_login() <django.test.Client.force_login>` or
:meth:`login() <django.test.Client.login()>` method before accessing a URL:

::

    def test_with_authenticated_client(client, django_user_model):
        username = "user1"
        password = "bar"
        user = django_user_model.objects.create_user(username=username, password=password)
        # Use this:
        client.force_login(user)
        # Or this:
        client.login(username=username, password=password)
        response = client.get('/private')
        assert response.content == 'Protected Area'

.. fixture:: async_client

``async_client`` - ``django.test.AsyncClient``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a `django.test.AsyncClient`_.

.. _django.test.AsyncClient: https://docs.djangoproject.com/en/stable/topics/testing/tools/#testing-asynchronous-code

Example
"""""""

This example uses `pytest-asyncio <https://github.com/pytest-dev/pytest-asyncio>`_.

::

    @pytest.mark.asyncio
    async def test_with_async_client(async_client):
        response = await async_client.get('/')
        assert response.content == 'Foobar'

.. fixture:: admin_client

``admin_client`` - ``django.test.Client`` logged in as admin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a :class:`django.test.Client`, logged in as an admin user.

Example
"""""""

::

    def test_an_admin_view(admin_client):
        response = admin_client.get('/admin/')
        assert response.status_code == 200

Using the `admin_client` fixture will cause the test to automatically be marked
for database use (no need to specify the :func:`~pytest.mark.django_db` mark).

.. fixture:: admin_user

``admin_user`` - an admin user (superuser)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a superuser, with username "admin" and password "password" (in
case there is no "admin" user yet).

Using the `admin_user` fixture will cause the test to automatically be marked
for database use (no need to specify the :func:`~pytest.mark.django_db` mark).

.. fixture:: django_user_model

``django_user_model``
~~~~~~~~~~~~~~~~~~~~~

A shortcut to the User model configured for use by the current Django project (aka the model referenced by
`settings.AUTH_USER_MODEL <https://docs.djangoproject.com/en/stable/ref/settings/#auth-user-model>`_).
Use this fixture to make pluggable apps testable regardless what User model is configured
in the containing Django project.

Example
"""""""

::

    def test_new_user(django_user_model):
        django_user_model.objects.create(username="someone", password="something")

.. fixture:: django_username_field

``django_username_field``
~~~~~~~~~~~~~~~~~~~~~~~~~

This fixture extracts the field name used for the username on the user model, i.e.
resolves to the user model's :attr:`~django.contrib.auth.models.CustomUser.USERNAME_FIELD`.
Use this fixture to make pluggable apps testable regardless what the username field
is configured to be in the containing Django project.

.. fixture:: db

``db``
~~~~~~~

This fixture will ensure the Django database is set up.  Only
required for fixtures that want to use the database themselves.  A
test function should normally use the :func:`pytest.mark.django_db`
mark to signal it needs the database. This fixture does
not return a database connection object. When you need a Django
database connection or cursor, import it from Django using
``from django.db import connection``.

.. fixture:: transactional_db

``transactional_db``
~~~~~~~~~~~~~~~~~~~~

This fixture can be used to request access to the database including
transaction support.  This is only required for fixtures which need
database access themselves.  A test function should normally use the
func:`pytest.mark.django_db`  mark with ``transaction=True`` to signal
it needs the database.

.. fixture:: django_db_reset_sequences

``django_db_reset_sequences``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This fixture provides the same transactional database access as
:fixture:`transactional_db`, with additional support for reset of auto
increment sequences (if your database supports it). This is only required for
fixtures which need database access themselves. A test function should normally
use the :func:`pytest.mark.django_db` mark with ``transaction=True`` and
``reset_sequences=True``.

.. fixture:: live_server

``live_server``
~~~~~~~~~~~~~~~

This fixture runs a live Django server in a background thread.  The
server's URL can be retrieved using the ``live_server.url`` attribute
or by requesting it's string value: ``str(live_server)``.  You can
also directly concatenate a string to form a URL: ``live_server +
'/foo``.

.. note:: Combining database access fixtures.

  When using multiple database fixtures together, only one of them is
  used.  Their order of precedence is as follows (the last one wins):

  * ``db``
  * ``transactional_db``
  * ``django_db_reset_sequences``

  In addition, using ``live_server`` will also trigger transactional
  database access, if not specified.

.. fixture:: settings

``settings``
~~~~~~~~~~~~

This fixture will provide a handle on the Django settings module, and
automatically revert any changes made to the settings (modifications, additions
and deletions).

Example
"""""""

::

    def test_with_specific_settings(settings):
        settings.USE_TZ = True
        assert settings.USE_TZ


.. fixture:: django_assert_num_queries

``django_assert_num_queries``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: django_assert_num_queries(num, connection=None, info=None)

  :param num: expected number of queries
  :param connection: optional non-default DB connection
  :param str info: optional info message to display on failure

This fixture allows to check for an expected number of DB queries.

If the assertion failed, the executed queries can be shown by using
the verbose command line option.

It wraps ``django.test.utils.CaptureQueriesContext`` and yields the wrapped
``CaptureQueriesContext`` instance.

Example usage::

    def test_queries(django_assert_num_queries):
        with django_assert_num_queries(3) as captured:
            Item.objects.create('foo')
            Item.objects.create('bar')
            Item.objects.create('baz')

        assert 'foo' in captured.captured_queries[0]['sql']


.. fixture:: django_assert_max_num_queries

``django_assert_max_num_queries``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: django_assert_max_num_queries(num, connection=None, info=None)

  :param num: expected maximum number of queries
  :param connection: optional non-default DB connection
  :param str info: optional info message to display on failure

This fixture allows to check for an expected maximum number of DB queries.

It is a specialized version of :fixture:`django_assert_num_queries`.

Example usage::

    def test_max_queries(django_assert_max_num_queries):
        with django_assert_max_num_queries(2):
            Item.objects.create('foo')
            Item.objects.create('bar')

.. fixture:: mailoutbox

``mailoutbox``
~~~~~~~~~~~~~~

A clean email outbox to which Django-generated emails are sent.

Example
"""""""

::

    from django.core import mail

    def test_mail(mailoutbox):
        mail.send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        assert len(mailoutbox) == 1
        m = mailoutbox[0]
        assert m.subject == 'subject'
        assert m.body == 'body'
        assert m.from_email == 'from@example.com'
        assert list(m.to) == ['to@example.com']


This uses the ``django_mail_patch_dns`` fixture, which patches
``DNS_NAME`` used by :py:mod:`django.core.mail` with the value from
the ``django_mail_dnsname`` fixture, which defaults to
"fake-tests.example.com".


Automatic cleanup
-----------------

pytest-django provides some functionality to assure a clean and consistent environment
during tests.

Clearing of site cache
~~~~~~~~~~~~~~~~~~~~~~

If ``django.contrib.sites`` is in your INSTALLED_APPS, Site cache will
be cleared for each test to avoid hitting the cache and causing the wrong Site
object to be returned by ``Site.objects.get_current()``.


Clearing of mail.outbox
~~~~~~~~~~~~~~~~~~~~~~~

``mail.outbox`` will be cleared for each pytest, to give each new test an empty
mailbox to work with. However, it's more "pytestic" to use the ``mailoutbox`` fixture described above
than to access ``mail.outbox``.
