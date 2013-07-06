pytest-django is a plugin for `pytest <http://pytest.org/>`_ that provides a set of useful tools for testing `Django <http://www.djangoproject.com/>`_ applications and projects.

Requirements
============

Supported Django versions: 1.3, 1.4 and 1.5

Supported Python versions 2.5 - 2.7 and 3.2 - 3.3. PyPy can also be used.

A recent version of pytest is required (>= 2.3.4).


Quick Start
===========
1. ``pip install pytest-django``
2. Make sure ``DJANGO_SETTINGS_MODULE`` is defined and and run tests with the ``py.test`` command.
3. (Optionally) If you put your tests under a tests directory (the standard Django application layout), and your files are not named ``test_FOO.py``, `see the FAQ <http://pytest-django.readthedocs.org/en/latest/faq.html#my-tests-are-not-being-picked-up-when-i-run-pytest-from-the-root-directory-why-not>`_


Documentation
==============

`Documentation is available on Read the Docs. <http://pytest-django.readthedocs.org/en/latest/index.html>`_


Why would I use this instead of Django's manage.py test command?
================================================================

Running the test suite with pytest offers some features that are not present in Djangos standard test mechanism:

 * `Smarter test discovery <http://pytest.org/latest/example/pythoncollection.html>`_ (no need for ``from .foo import *`` in your test modules).
 * Less boilerplate: no need to import unittest, create a subclass with methods. Just write tests as regular functions.
 * `Injection of test depencies with funcargs <http://pytest.org/latest/funcargs.html>`_
 * No need to run all tests, `it is easy to specify which tests to run <http://pytest.org/latest/usage.html#specifying-tests-selecting-tests>`_.
 * Database re-use: no need to re-create the test database for every test run.
 * No hacks required to only run your apps, and not the 3rd party/contrib apps that is listed in your ``INSTALLED_APPS``.
 * There are a lot of other nice plugins available for pytest.
 * No pain of switching: Existing unittest-style tests will still work without any modifications.

See the `pytest documentation <http://pytest.org/latest/>`_ for more information on pytest.


Bugs? Feature suggestions?
============================
Report issues and feature requests at the `github issue tracker <http://github.com/pelme/pytest_django/issues>`_.
