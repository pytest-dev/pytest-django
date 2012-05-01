Getting started
===============

Installation
------------

pytest-django is available directly from `PyPi <http://pypi.python.org/pypi/pytest-django>`_, and can be easily installed with ``pip``::

    pip install pytest-django

``pytest-django`` uses ``py.test``'s module system and can be used right away after installation, there is nothing more to configure.

Usage
-----

Tests are invoked directly with the `py.test` command, instead of ``manage.py test``/``django-admin.py test``::

    py.test

The environment variable ``DJANGO_SETTINGS_MODULE`` must be set in order for py.test to find your project settings.

To run with a specific settings module, use::

    DJANGO_SETTINGS_MODULE=foo.settings py.test

`py.test` will find tests in your project automatically, ``INSTALLED_APPS`` will not be consulted. This means that 3rd-party and django.contrib.* apps will not be picked up by the test runner.

Don't like typing out DJANGO_SETTINGS_MODULE=...? See :ref:`faq-django-settings-module`.

If you are interested in how to select specific tests, format tracebacks in different way, see `the excellent py.test documentation <http://pytest.org/>`_.
