Django helpers
==============


funcargs
--------

pytest-django provides some pytest funcargs to provide depencies for tests. More information on funcargs is available in the `py.test documentation <http://pytest.org/latest/funcargs.html>`_


``rf`` - ``RequestFactory``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of a `django.test.client.RequestFactory <https://docs.djangoproject.com/en/dev/topics/testing/#django.test.client.RequestFactory>`_.

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
An instance of a `django.test.Client <https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client>`_.

Example
"""""""

::

    def test_with_client(client):
        response = client.get('/')
        assert response.content == 'Foobar'


``admin_client`` - ``django.test.Client`` logged in as admin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
An instance of a `django.test.Client <https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client>`_, that is logged in as an admin user.

Example
"""""""

::

    def test_an_admin_view(admin_client):
        response = admin_client.get('/admin/')
        assert response.status_code == 200

As an extra bonus this will automatically mark the database using the
``djangodb`` mark.


Markers
-------

``pytest-django`` registers and uses two markers.  See the py.test
documentation_ on what marks and and for notes on using_ them.

.. _documentation: http://pytest.org/latest/mark.html
.. _using: http://pytest.org/latest/example/markers.html#marking-whole-classes-or-modules


.. py:function:: pytest.mark.djangodb(transaction=False, multidb=False)

   This is used to mark a test function as requiring the database.  It
   will ensure the database is setup correctly for the test.  Any test
   not marked with ``djangodb`` which tries to use the database will
   fail.

   The *transaction* argument will allow the test to use
   transactions.  Without it transaction operations are noops during
   the test.

   The *multidb* argument will ensure all tests databases are setup.
   Normally only the default database is setup.

.. py:function:: pytest.mark.urls(urls)

   Specify a different URL conf module for the marked tests.  *urls*
   is a string pointing to a module, e.g. ``myapp.test_urls``.  This
   is similar to Django's ``TestCase.urls`` attribute.


decorators
----------

Decorators are deprecated and have been replaced with ``py.test``
marks.


``transaction_test_case``
~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 1.4
   Use :func:`pytest.mark.djangodb` instead.

When writing unittest style tests, Django's `django.test.TestCase <https://docs.djangoproject.com/en/dev/topics/testing/#django.test.TestCase>`_ or
`django.test.TransactionTestCase <https://docs.djangoproject.com/en/dev/topics/testing/#django.test.TransactionTestCase>`_ is the easiest way of
writing test cases which gets a clean test database.

When transaction behaviour is being tested, the ``transaction_test_case`` decorator can be used (will have the same effect as using `TransactionTestCase <https://docs.djangoproject.com/en/dev/topics/testing/#django.test.TransactionTestCase>`_)::

    from pytest_django import transaction_test_case

    @transaction_test_case
    def test_database_interaction_with_real_transactions():
        # This code will not be wrapped in a transaction. Transaction commits/rollbacks
        # can be tested here. After execution of this test case, the database will be flushed
        # and reset to its original state.
        pass

``pytest.urls``
~~~~~~~~~~~~~~~

.. deprecated:: 1.4
   Use :func:`pytest.mark.urls` instead.


A decorator to change the URLconf for a particular test, similar to the `urls` attribute on Django's `TestCase`.

Example
"""""""

::

    @pytest.urls('myapp.test_urls')
    def test_something(client):
        assert 'Success!' in client.get('/some_path/')
