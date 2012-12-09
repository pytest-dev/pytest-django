Configuring Django settings
===========================

There are a couple of different ways Django settings can be provided for
the tests.

The environment variable ``DJANGO_SETTINGS_MODULE``
---------------------------------------------------

Running the tests with DJANGO_SETTINGS_MODULE defined will find the
Django settings the same way Django does by default.

Example::

    $ export DJANGO_SETTINGS_MODULE=test_settings
    $ py.test

or::

    $ DJANGO_SETTINGS_MODULE=test_settings py.test


Command line option ``--ds=SETTINGS``
-------------------------------------

Example::

    $ py.test --ds=test_settings


pytest.ini settings
-------------------

Example contents of pytest.ini::

    [pytest]
    DJANGO_SETTINGS_MODULE = test_settings

Using ``django.conf.settings.configure()``
------------------------------------------

Django settings can be set up by calling ``django.conf.settings.configure()``.

This can be done from your project's ``conftest.py`` file::

    from django.conf import settings

    def pytest_configure():
        settings.configure(DATABASES=...)

