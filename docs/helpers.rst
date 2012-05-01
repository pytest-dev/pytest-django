Django helpers
==============


funcargs
--------

pytest-django provides some pytest funcargs to provide depencies for tests. More information on funcargs is available in the `py.test documentation <http://pytest.org/latest/funcargs.html>`_


rf
~~
An instance of a `django.test.client.RequestFactory <https://docs.djangoproject.com/en/dev/topics/testing/#django.test.client.RequestFactory>`_.

Example
"""""""

::

    from myapp.views import my_view

    def test_details(rf):
        request = rf.get('/customer/details')
        response = my_view(request)
        assert response.status_code == 200

client
~~~~~~
An instance of a `django.test.client.Client <https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client>`_.

Example
"""""""

::

    def test_with_client(client):
        response = client.get('/')
        assert response.content == 'Foobar'


admin_client
~~~~~~~~~~~~
An instance of a `django.test.client.Client <https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client>`_, that is logged in as an admin user.

Example
"""""""

::

    def test_an_admin_view(admin_client):
        response = admin_client.get('/admin/')
        assert response.status_code == 200



decorators
----------

transaction_test_case
~~~~~~~~~~~~~~~~~~~~~

When writing unittest style tests, Django's `django.test.TestCase <https://docs.djangoproject.com/en/dev/topics/testing/#django.test.TestCase> or
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

pytest.urls
~~~~~~~~~~~
A decorator to change the URLconf for a particular test, similar to the `urls` attribute on Django's `TestCase`.

Example
"""""""

::

    @pytest.urls('myapp.test_urls')
    def test_something(client):
        assert 'Success!' in client.get('/some_path/')
