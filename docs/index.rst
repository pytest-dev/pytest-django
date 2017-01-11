===========================
pytest-django Documentation
===========================

pytest-django is a plugin for `pytest`_ that provides a set of useful tools
for testing `Django`_ applications and projects.

.. _pytest: http://pytest.org/
.. _Django: https://www.djangoproject.com/

Quick Start
===========

1. ``pip install pytest-django``
2. Make sure ``DJANGO_SETTINGS_MODULE`` is defined and and run tests with the ``pytest`` command.
3. (Optional) If you want tests of Django's default application layout be discovered (``tests.py``),
   if you put your tests under a ``tests/`` directory , or your files are not named ``test_FOO.py``,
   see the FAQ at :ref:`faq-tests-not-being-picked-up`.

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

Why would I use this instead of Django's manage.py test command?
================================================================

Running the test suite with pytest offers some features that are not present in Django's standard test mechanism:

* Less boilerplate: no need to import unittest, create a subclass with methods. Just write tests as regular functions.
* `Manage test dependencies with fixtures`_.
* Database re-use: no need to re-create the test database for every test run.
* Run tests in multiple processes for increased speed.
* There are a lot of other nice plugins available for pytest.
* Easy switching: Existing unittest-style tests will still work without any modifications.

See the `pytest documentation`_ for more information on pytest.

.. _Manage test dependencies with fixtures: http://docs.pytest.org/en/latest/fixture.html
.. _pytest documentation: http://docs.pytest.org/

Bugs? Feature suggestions?
==========================

Report issues and feature requests at the `GitHub issue tracker`_.

.. _GitHub issue tracker: http://github.com/pytest-dev/pytest-django/issues

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
