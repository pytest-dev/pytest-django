.. _configuring_django_settings:

Configuring Django settings
===========================

There are a couple of different ways Django settings can be provided for
the tests.

The environment variable ``DJANGO_SETTINGS_MODULE``
---------------------------------------------------

Running the tests with ``DJANGO_SETTINGS_MODULE`` defined will find the
Django settings the same way Django does by default.

Example::

    $ export DJANGO_SETTINGS_MODULE=test.settings
    $ pytest

or::

    $ DJANGO_SETTINGS_MODULE=test.settings pytest


Command line option ``--ds=SETTINGS``
-------------------------------------

Example::

    $ pytest --ds=test.settings


``pytest.ini`` settings
-----------------------

Example contents of pytest.ini::

    [pytest]
    DJANGO_SETTINGS_MODULE = test.settings

``pyproject.toml`` settings
---------------------------

Example contents of pyproject.toml::

    [tool.pytest.ini_options]
    DJANGO_SETTINGS_MODULE = "test.settings"

Order of choosing settings
--------------------------

The order of precedence is, from highest to lowest:

* The command line option ``--ds``
* The environment variable ``DJANGO_SETTINGS_MODULE``
* The ``DJANGO_SETTINGS_MODULE`` option in the configuration file -
  ``pytest.ini``, or other file that Pytest finds such as ``tox.ini`` or ``pyproject.toml``

If you want to use the highest precedence in the configuration file, you can
use ``addopts = --ds=yourtestsettings``.

Using django-configurations
---------------------------

There is support for using `django-configurations <https://pypi.python.org/pypi/django-configurations/>`_.

To do so configure the settings class using an environment variable, the
``--dc`` flag, ``pytest.ini`` option ``DJANGO_CONFIGURATION`` or ``pyproject.toml`` option ``DJANGO_CONFIGURATION``.

Environment Variable::

    $ export DJANGO_CONFIGURATION=MySettings
    $ pytest

Command Line Option::

    $ pytest --dc=MySettings

INI File Contents::

    [pytest]
    DJANGO_CONFIGURATION=MySettings

pyproject.toml File Contents::

    [tool.pytest.ini_options]
    DJANGO_CONFIGURATION = "MySettings"

Using ``django.conf.settings.configure()``
------------------------------------------

In case there is no ``DJANGO_SETTINGS_MODULE``, the ``settings`` object can be
created by calling ``django.conf.settings.configure()``.

This can be done from your project's ``conftest.py`` file::

    from django.conf import settings

    def pytest_configure():
        settings.configure(DATABASES=...)

Overriding individual settings
------------------------------

Settings can be overridden by using the :fixture:`settings` fixture::

    @pytest.fixture(autouse=True)
    def use_dummy_cache_backend(settings):
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            }
        }

Here `autouse=True` is used, meaning the fixture is automatically applied to all tests,
but it can also be requested individually per-test.

Changing your app before Django gets set up
-------------------------------------------

pytest-django calls :func:`django.setup` automatically.  If you want to do
anything before this, you have to create a pytest plugin and use
the :func:`~_pytest.hookspec.pytest_load_initial_conftests` hook, with
``tryfirst=True``, so that it gets run before the hook in pytest-django
itself::

    @pytest.hookimpl(tryfirst=True)
    def pytest_load_initial_conftests(early_config, parser, args):
        import project.app.signals

        def noop(*args, **kwargs):
            pass

        project.app.signals.something = noop

This plugin can then be used e.g. via ``-p`` in :pytest-confval:`addopts`.
