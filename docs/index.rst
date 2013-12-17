Welcome to pytest-django's documentation!
=========================================

pytest-django is a plugin for `py.test <http://pytest.org/>`_ that provides a set of useful tools for testing `Django <http://www.djangoproject.com/>`_ applications and projects.

.. toctree::
   :maxdepth: 3

   tutorial
   configuring_django
   database
   helpers
   faq
   contributing
   changelog

Why would I use this instead of Django's manage.py test command?
================================================================

Running the test suite with py.test offers some features that are not present in Djangos standard test mechanism:

 * `Smarter test discovery <http://pytest.org/latest/example/pythoncollection.html>`_ (no need for ``from .foo import *`` in your test modules).
 * Less boilerplate: no need to import unittest, create a subclass with methods. Just write tests as regular functions.
 * `Injection of test depencies with funcargs <http://pytest.org/latest/funcargs.html>`_
 * No need to run all tests, `it is easy to specify which tests to run <http://pytest.org/latest/usage.html#specifying-tests-selecting-tests>`_.
 * No hacks required to only run your apps, and not the 3rd party/contrib apps that is listed in your ``INSTALLED_APPS``.
 * There are a lot of other nice plugins available for py.test.
 * No pain of switching: Existing unittest-style tests will still work without any modifications.

See the `py.test documentation <http://pytest.org/latest/>`_ for more information on py.test.

Quick Start
===========
1. ``pip install pytest-django``
2. Make sure ``DJANGO_SETTINGS_MODULE`` is defined and and run tests with the ``py.test`` command.
3. (Optionally) If you put your tests under a tests directory (the standard Django application layout), and your files are not named ``test_FOO.py``, see the FAQ :ref:`faq-tests-not-being-picked-up`.


Requirements
============

The current supported versions of Python, Django and pytest are:

 * Python 2.6-2.7
 * Django 1.3-1.6
 * py.test 2.3.4+


Bugs? Feature suggestions?
============================
Report issues and feature requests at the `github issue tracker <http://github.com/pelme/pytest_django/issues>`_.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
