Django helpers
==============


funcargs
--------

pytest-django provides some pytest funcargs to provide depencies for tests.
More information on funcargs is available in the `py.test documentation
<http://pytest.org/latest/funcargs.html>`_


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

``djangodb`` 
~~~~~~~~~~~~~

This funcarg will ensure the Django database is set up.  This only
required for funcargs which want to use the database themselves.  A
test function should normally use the :py:func:`~pytest.mark.djangodb`
mark to signal it needs the database.


Markers
-------

``pytest-django`` registers and uses markers.  See the py.test documentation_
on what marks and and for notes on using_ them.

.. _documentation: http://pytest.org/latest/mark.html
.. _using: http://pytest.org/latest/example/markers.html#marking-whole-classes-or-modules


.. py:function:: pytest.mark.djangodb([transaction=False, multidb=False])

   This is used to mark a test function as requiring the database.  It
   will ensure the database is setup correctly for the test.
   
   Any test not marked with ``djangodb`` which tries to use the database will
   fail.

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

   :type multidb: bool
   :param multidb:
     The ``multidb`` argument will ensure all tests databases are setup.
     Normally only the ``default`` database alias is setup.

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

