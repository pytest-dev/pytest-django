Django helpers
==============

Markers
-------

``pytest-django`` registers and uses markers.  See the py.test documentation_
on what marks and and for notes on using_ them.

.. _documentation: http://pytest.org/latest/mark.html
.. _using: http://pytest.org/latest/example/markers.html#marking-whole-classes-or-modules


.. py:function:: pytest.mark.django_db([transaction=False])

   This is used to mark a test function as requiring the database.  It
   will ensure the database is setup correctly for the test.

   In order for a test to have access to the database it must either
   be marked using the ``django_db`` mark or request one of the ``db``
   or ``transcational_db`` fixtures.  Otherwise the test will fail
   when trying to access the database.

   :type transaction: bool
   :param transaction:
     The ``transaction`` argument will allow the test to use real transactions.
     With ``transaction=False`` (the default when not specified), transaction
     operations are noops during the test. This is the same behavior that
     `django.test.TestCase
     <https://docs.djangoproject.com/en/dev/topics/testing/#django.test.TestCase>`_
     uses. When ``transaction=True``, the behavior will be the same as
     `django.test.TransactionTestCase
     <https://docs.djangoproject.com/en/dev/topics/testing/#django.test.TransactionTestCase>`_

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


Fixtures
--------

pytest-django provides some pytest fixtures to provide depencies for tests.
More information on fixtures is available in the `py.test documentation
<http://pytest.org/latest/fixture.html>`_.


``rf`` - ``RequestFactory``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a `django.test.client.RequestFactory
<https://docs.djangoproject.com/en/dev/topics/testing/#django.test.client.RequestFactory>`_.

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

An instance of a `django.test.Client
<https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client>`_.

Example
"""""""

::

    def test_with_client(client):
        response = client.get('/')
        assert response.content == 'Foobar'


``admin_client`` - ``django.test.Client`` logged in as admin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a `django.test.Client
<https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client>`_,
that is logged in as an admin user.

Example
"""""""

::

    def test_an_admin_view(admin_client):
        response = admin_client.get('/admin/')
        assert response.status_code == 200

As an extra bonus this will automatically mark the database using the
``djangodb`` mark.

``db``
~~~~~~~

This fixture will ensure the Django database is set up.  This only
required for fixtures which want to use the database themselves.  A
test function should normally use the :py:func:`~pytest.mark.djangodb`
mark to signal it needs the database.

``transactional_db``
~~~~~~~~~~~~~~~~~~~~

This fixture can be used to request access to the database including
transaction support.  This is only required for fixtures which need
database access themselves.  A test function would normally use the
:py:func:`~pytest.mark.djangodb` mark to signal it needs the database.

``live_server``
~~~~~~~~~~~~~~~

This fixture runs a live Django server in a background thread.  The
server's URL can be retreived using the ``live_server.url`` attribute
or by requesting it's string value: ``unicode(live_server)``.  You can
also directly concatenate a string to form a URL: ``live_server +
'/foo``.
