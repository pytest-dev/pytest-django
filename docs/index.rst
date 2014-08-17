Welcome to pytest-django's documentation!
=========================================

pytest-django is a plugin for `py.test <http://pytest.org/>`_ that provides a set of useful tools for testing `Django <http://www.djangoproject.com/>`_ applications and projects.

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

Why would I use this instead of Django's manage.py test command?
================================================================

Running the test suite with py.test offers some features that are not present in Django's standard test mechanism:

 * Less boilerplate: no need to import unittest, create a subclass with methods. Just write tests as regular functions.
 * `Manage test dependencies with fixtures <http://pytest.org/latest/fixture.html>`_
 * Database re-use: no need to re-create the test database for every test run.
 * Run tests in multiple processes for increased speed
 * There are a lot of other nice plugins available for pytest.
 * Easy switching: Existing unittest-style tests will still work without any modifications.

See the `py.test documentation <http://pytest.org/latest/>`_ for more information on py.test.

Quick Start
===========
1. ``pip install pytest-django``
2. Make sure ``DJANGO_SETTINGS_MODULE`` is defined and and run tests with the ``py.test`` command.
3. (Optionally) If you put your tests under a tests directory (the standard Django application layout), and your files are not named ``test_FOO.py``, see the FAQ :ref:`faq-tests-not-being-picked-up`.


Bugs? Feature suggestions?
============================
Report issues and feature requests at the `github issue tracker <http://github.com/pelme/pytest_django/issues>`_.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
