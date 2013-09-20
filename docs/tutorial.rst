Getting started
===============

Andreas Pelme gave a talk at EuroPython 2013 on testing in Django with
py.test. It shows the benefits of using py.test and how to get started:

`Testing Django application with py.test (YouTube link) <http://www.youtube.com/watch?v=aUf8Fkb7TaY>`_

Installation
------------

pytest-django is available directly from `PyPi <http://pypi.python.org/pypi/pytest-django>`_, and can be easily installed with ``pip``::

    pip install pytest-django

``pytest-django`` uses ``py.test``'s module system and can be used right away after installation, there is nothing more to configure.

Usage
-----

Tests are invoked directly with the ``py.test`` command, instead of ``manage.py test``/``django-admin.py test``::

    py.test

Django needs the environment variable ``DJANGO_SETTINGS_MODULE`` set
for tests runs to work.  This plugin allows you to specify this in
multiple ways:

1. Using the ``--ds`` command line option.
2. By writing a ``DJANGO_SETTINGS_MODULE`` setting in the ``[pytest]``
   section of your `py.test configuration file
   <http://pytest.org/latest/customize.html?#how-test-configuration-is-read-from-configuration-ini-files>`_
3. By using the ``DJANGO_SETTINGS_MODULE`` environment variable.

`py.test` will find tests in your project automatically, ``INSTALLED_APPS`` will not be consulted. This means that 3rd-party and django.contrib.* apps will not be picked up by the test runner.

If you use virtualenv you can automatically use the environment
variable.  See :ref:`faq-django-settings-module`.

If you are interested in how to select specific tests, format tracebacks in different way, see `the excellent py.test documentation <http://pytest.org/>`_.
