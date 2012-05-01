Getting started
===============

Installation
------------

pytest-djangos is available at `PyPi <http://pypi.python.org/pypi/pytest-django>`_,
the preffered installation method is with pip::

    pip install pytest-django

``pytest-django`` uses ``py.test``'s module system and can be used right away after installation, there is nothing more to enable.

Usage
-----

Tests are invoked directly with the `py.test` command, instead of ``manage.py test``/``django-admin.py test``::

    DJANGO_SETTINGS_MODULE=settings py.test

Don't like typing out DJANGO_SETTINGS_MODULE=...? See :ref:`faq-django-settings-module`.

