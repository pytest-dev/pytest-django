===========================
pytest-django Documentation
===========================

pytest-django is a plugin for `pytest`_ that provides a set of useful tools
for testing `Django`_ applications and projects.

.. _pytest: https://pytest.org/
.. _Django: https://www.djangoproject.com/

Quick Start
===========

.. code-block:: bash

   $ pip install pytest-django

Make sure ``DJANGO_SETTINGS_MODULE`` is defined (see
:ref:`configuring_django_settings`) and make your tests discoverable
(see :ref:`faq-tests-not-being-picked-up`):

.. code-block:: ini

   # -- FILE: pytest.ini (or tox.ini)
   [pytest]
   DJANGO_SETTINGS_MODULE = test_settings
   # -- recommended but optional:
   python_files = tests.py test_*.py *_tests.py

Run your tests with ``pytest``:

.. code-block:: bash

   $ pytest

Why would I use this instead of Django's manage.py test command?
================================================================

Running the test suite with pytest offers some features that are not present in Django's standard test mechanism:

* Less boilerplate: no need to import unittest, create a subclass with methods. Just write tests as regular functions.
* `Manage test dependencies with fixtures`_.
* Run tests in multiple processes for increased speed.
* There are a lot of other nice plugins available for pytest.
* Easy switching: Existing unittest-style tests will still work without any modifications.

See the `pytest documentation`_ for more information on pytest.

.. _Manage test dependencies with fixtures: http://docs.pytest.org/en/latest/fixture.html
.. _pytest documentation: http://docs.pytest.org/

Bugs? Feature Suggestions?
==========================

Report issues and feature requests at the `GitHub issue tracker`_.

.. _GitHub issue tracker: http://github.com/pytest-dev/pytest-django/issues

Table of Contents
=================

.. toctree::
   :maxdepth: 3

   tutorial
   configuring_django
   managing_python_path
   usage
   database
   helpers
   faq
   contributing
   changelog

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
