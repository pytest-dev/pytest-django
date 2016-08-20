.. _helpers:

Django helpers
==============

Markers
-------

``pytest-django`` registers and uses markers.  See the pytest documentation_
on what marks are and for notes on using_ them.

.. _documentation: http://pytest.org/latest/mark.html
.. _using: http://pytest.org/latest/example/markers.html#marking-whole-classes-or-modules


``pytest.mark.django_db(transaction=False)`` - request database access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. :py:function:: pytest.mark.django_db:

This is used to mark a test function as requiring the database. It
will ensure the database is setup correctly for the test. Each test
will run in its own transaction which will be rolled back at the end
of the test. This behavior is the same as Django's standard
`django.test.TestCase`_ class.

In order for a test to have access to the database it must either
be marked using the ``django_db`` mark or request one of the ``db``
or ``transactional_db`` fixtures.  Otherwise the test will fail
when trying to access the database.

:type transaction: bool
:param transaction:
 The ``transaction`` argument will allow the test to use real transactions.
 With ``transaction=False`` (the default when not specified), transaction
 operations are noops during the test. This is the same behavior that
 `django.test.TestCase`_
 uses. When ``transaction=True``, the behavior will be the same as
 `django.test.TransactionTestCase`_

.. note::

  If you want access to the Django database *inside a fixture*
  this marker will not help even if the function requesting your
  fixture has this marker applied.  To access the database in a
  fixture, the fixture itself will have to request the ``db`` or
  ``transactional_db`` fixture.  See below for a description of
  them.

.. note:: Automatic usage with ``django.test.TestCase``.

 Test classes that subclass `django.test.TestCase`_ will have access to
 the database always to make them compatible with existing Django tests.
 Test classes that subclass Python's ``unittest.TestCase`` need to have the
 marker applied in order to access the database.

.. _django.test.TestCase: https://docs.djangoproject.com/en/dev/topics/testing/overview/#testcase
.. _django.test.TransactionTestCase: https://docs.djangoproject.com/en/dev/topics/testing/overview/#transactiontestcase


``pytest.mark.urls`` - override the urlconf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: pytest.mark.urls(urls)

   Specify a different ``settings.ROOT_URLCONF`` module for the marked tests.

   :type urls: string
   :param urls:
     The urlconf module to use for the test, e.g. ``myapp.test_urls``.  This is
     similar to Django's ``TestCase.urls`` attribute.

   Example usage::

     @pytest.mark.urls('myapp.test_urls')
     def test_something(client):
         assert 'Success!' in client.get('/some_url_defined_in_test_urls/')


``pytest.mark.ignore_template_errors`` - ignore invalid template variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: pytest.mark.ignore_template_errors

  If you run pytest using the ``--fail-on-template-vars`` option,
  tests will fail should your templates contain any invalid variables.
  This marker will disable this feature by setting ``settings.TEMPLATE_STRING_IF_INVALID=None``
  or the ``string_if_invalid`` template option in Django>=1.7

  Example usage::

     @pytest.mark.ignore_template_errors
     def test_something(client):
         client('some-url-with-invalid-template-vars')


Fixtures
--------

pytest-django provides some pytest fixtures to provide dependencies for tests.
More information on fixtures is available in the `pytest documentation
<http://pytest.org/latest/fixture.html>`_.


``rf`` - ``RequestFactory``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a `django.test.RequestFactory`_

.. _django.test.RequestFactory: https://docs.djangoproject.com/en/dev/topics/testing/advanced/#django.test.RequestFactory

Example
"""""""

::

    from myapp.views import my_view

    def test_details(rf):
        request = rf.get('/customer/details')
        response = my_view(request)
        assert response.status_code == 200

``client`` - ``django.test.Client``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a `django.test.Client`_

.. _django.test.Client: https://docs.djangoproject.com/en/dev/topics/testing/tools/#the-test-client

Example
"""""""

::

    def test_with_client(client):
        response = client.get('/')
        assert response.content == 'Foobar'


``admin_client`` - ``django.test.Client`` logged in as admin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a `django.test.Client`_,
that is logged in as an admin user.

Example
"""""""

::

    def test_an_admin_view(admin_client):
        response = admin_client.get('/admin/')
        assert response.status_code == 200

As an extra bonus this will automatically mark the database using the
``django_db`` mark.

``admin_user`` - a admin user (superuser)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a superuser, with username "admin" and password "password" (in
case there is no "admin" user yet).

As an extra bonus this will automatically mark the database using the
``django_db`` mark.

``django_user_model``
~~~~~~~~~~~~~~~~~~~~~

The user model used by Django. This handles different versions of Django.

``django_username_field``
~~~~~~~~~~~~~~~~~~~~~~~~~

The field name used for the username on the user model.

``db``
~~~~~~~

.. fixture:: db

This fixture will ensure the Django database is set up.  This only
required for fixtures which want to use the database themselves.  A
test function should normally use the :py:func:`~pytest.mark.django_db`
mark to signal it needs the database.

``transactional_db``
~~~~~~~~~~~~~~~~~~~~

This fixture can be used to request access to the database including
transaction support.  This is only required for fixtures which need
database access themselves.  A test function would normally use the
:py:func:`~pytest.mark.django_db` mark to signal it needs the database.

``live_server``
~~~~~~~~~~~~~~~

This fixture runs a live Django server in a background thread.  The
server's URL can be retrieved using the ``live_server.url`` attribute
or by requesting it's string value: ``unicode(live_server)``.  You can
also directly concatenate a string to form a URL: ``live_server +
'/foo``.

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
