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
    $ pytest

or::

    $ DJANGO_SETTINGS_MODULE=test_settings pytest


Command line option ``--ds=SETTINGS``
-------------------------------------

Example::

    $ pytest --ds=test_settings


pytest.ini settings
-------------------

Example contents of pytest.ini::

    [pytest]
    DJANGO_SETTINGS_MODULE = test_settings

Order of choosing settings
--------------------------

When the command option `--ds`, the environment variable and the pytest.ini
configuration is used at the same time, pytest-django will prefer using
settings from the command line option `--ds`, then the environment variable and
last the pytest.ini.
You can use `addopts = --ds=yourtestsettings` in your pytest configuration
to automatically add the `--ds` option.

Using django-configurations
---------------------------

There is support for using `django-configurations <https://pypi.python.org/pypi/django-configurations/>`_.

To do so configure the settings class using an environment variable, the --dc
flag, or pytest.ini DJANGO_CONFIGURATION.

Environment Variable::

    $ export DJANGO_CONFIGURATION=MySettings
    $ pytest

Command Line Option::

    $ pytest --dc=MySettings


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

