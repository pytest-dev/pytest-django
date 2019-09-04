Getting started with pytest and pytest-django
=============================================

Introduction
------------

pytest and pytest-django are compatible with standard Django test suites and
Nose test suites. They should be able to pick up and run existing tests without
any or little configuration. This section describes how to get started quickly.

Talks, articles and blog posts
------------------------------

 * Talk from DjangoCon Europe 2014: `pytest: helps you write better Django apps, by Andreas Pelme <https://www.youtube.com/watch?v=aaArYVh6XSM>`_

 * Talk from EuroPython 2013: `Testing Django application with pytest, by Andreas Pelme <http://www.youtube.com/watch?v=aUf8Fkb7TaY>`_

 * Three part blog post tutorial (part 3 mentions Django integration): `pytest: no-boilerplate testing, by Daniel Greenfeld <http://pydanny.com/pytest-no-boilerplate-testing.html>`_

 * Blog post: `Django Projects to Django Apps: Converting the Unit Tests, by
   John Costa
   <https://www.johnmcostaiii.net/post/2013-04-21-django-projects-to-django-apps-converting-the-unit-tests/>`_.

For general information and tutorials on pytest, see the `pytest tutorial page <https://pytest.org/en/latest/getting-started.html>`_.


Step 1: Installation
--------------------

pytest-django can be obtained directly from `PyPI
<http://pypi.python.org/pypi/pytest-django>`_, and can be installed with
``pip``:

.. code-block:: bash

    pip install pytest-django

Installing pytest-django will also automatically install the latest version of
pytest. ``pytest-django`` uses ``pytest``'s plugin system and can be used right away
after installation, there is nothing more to configure.

Step 2: Point pytest to your Django settings
--------------------------------------------

You need to tell pytest which Django settings that should be used for test
runs. The easiest way to achieve this is to create a pytest configuration file
with this information.

Create a file called ``pytest.ini`` in your project root directory that
contains:

.. code-block:: ini

    [pytest]
    DJANGO_SETTINGS_MODULE = yourproject.settings

You can also specify your Django settings by setting the
``DJANGO_SETTINGS_MODULE`` environment variable or specifying the
``--ds=yourproject.settings`` command line flag when running the tests.
See the full documentation on :ref:`configuring_django_settings`.

Optionally, also add the following line to the ``[pytest]`` section to
instruct pytest to collect tests in Django's default app layouts, too.
See the FAQ at :ref:`faq-tests-not-being-picked-up` for more infos.

.. code-block:: ini

    python_files = tests.py test_*.py *_tests.py

Step 3: Run your test suite
---------------------------

Tests are invoked directly with the ``pytest`` command, instead of ``manage.py
test``, that you might be used to:

.. code-block:: bash

    pytest

Do you have problems with pytest not finding your code? See the FAQ
:ref:`faq-import-error`.

Next steps
----------

The :ref:`usage` section describes more ways to interact with your test suites.

pytest-django also provides some :ref:`helpers` to make it easier to write
Django tests.

Consult the `pytest documentation <https://pytest.org/>`_ for more information
on pytest itself.

Stuck? Need help?
-----------------

No problem, see the FAQ on :ref:`faq-getting-help` for information on how to
get help.
