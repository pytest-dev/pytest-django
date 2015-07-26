.. _configuring_django_settings:

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


Using django-configurations
---------------------------

There is support for using `django-configurations <https://pypi.python.org/pypi/django-configurations/>`_.

To do so configure the settings class using an environment variable, the --dc
flag, or pytest.ini DJANGO_CONFIGURATION.

Environment Variable::

    $ export DJANGO_CONFIGURATION=MySettings
    $ py.test

Command Line Option::

    $ py.test --dc=MySettings


INI File Contents::

    [pytest]
    DJANGO_CONFIGURATION=MySettings

Using ``django.conf.settings.configure()``
------------------------------------------

Django settings can be set up by calling ``django.conf.settings.configure()``.

This can be done from your project's ``conftest.py`` file::

    from django.conf import settings

    def pytest_configure():
        settings.configure(DATABASES=...)


``DEBUG`` setting during the test run
-------------------------------------

Default django test runner behavior is to force DEBUG setting to False. So does the ``pytest-django``.
But sometimes, especially for functional tests, you might want to avoid this, to debug why certain page does not work.

Command Line Option::

    $ py.test --no-force-no-debug

will make sure that DEBUG is not forced to False, so you can set it to True in your test settings.
