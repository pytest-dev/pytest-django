FAQ
===

.. _faq-import-error:

I see an error saying "could not import myproject.settings"
-----------------------------------------------------------

pytest-django tries to automatically add your project to the Python path by
looking for a ``manage.py`` file and adding its path to the Python path.

If this for some reason fails for you, you have to manage your Python paths
explicitly. See the documentation on :ref:`managing_the_python_path_explicitly`
for more information.

.. _faq-test-tags:

Are Django test tags supported?
-------------------------------

Yes, Django :ref:`test tagging <django:topics-tagging-tests>` is supported.
The Django test tags are automatically converted to :ref:`Pytest markers
<pytest:mark examples>`.

How can I make sure that all my tests run with a specific locale?
-----------------------------------------------------------------

Create a :ref:`pytest fixture <pytest:fixtures>` that is
automatically run before each test case. To run all tests with the English
locale, put the following code in your project's
:ref:`conftest.py <pytest:plugins>` file:

.. code-block:: python

    from django.utils.translation import activate

    @pytest.fixture(autouse=True)
    def set_default_language():
        activate('en')

.. _faq-tests-not-being-picked-up:

My tests are not being found. Why?
----------------------------------

By default, pytest looks for tests in files named ``test_*.py`` (note that
this is not the same as ``test*.py``) and ``*_test.py``.  If you have your
tests in files with other names, they will not be collected.  Note that
Django's ``startapp`` manage command creates an ``app_dir/tests.py`` file.
Also, it is common to put tests under ``app_dir/tests/views.py``, etc.

To find those tests, create a ``pytest.ini`` file in your project root and add
an appropriate ``python_files`` line to it:

.. code-block:: ini

    [pytest]
    python_files = tests.py test_*.py *_tests.py

See the `related pytest docs`_ for more details.

When debugging test collection problems, the ``--collectonly`` flag and
``-rs`` (report skipped tests) can be helpful.

.. _related pytest docs:
    https://docs.pytest.org/en/stable/example/pythoncollection.html#changing-naming-conventions

Does pytest-django work with the pytest-xdist plugin?
-----------------------------------------------------

Yes. pytest-django supports running tests in parallel with pytest-xdist. Each
process created by xdist gets its own separate database that is used for the
tests. This ensures that each test can run independently, regardless of whether
transactions are tested or not.

.. _faq-getting-help:

How can I use ``manage.py test`` with pytest-django?
----------------------------------------------------

pytest-django is designed to work with the ``pytest`` command, but if you
really need integration with ``manage.py test``, you can create a simple
test runner like this:

.. code-block:: python

    class PytestTestRunner:
        """Runs pytest to discover and run tests."""

        def __init__(self, verbosity=1, failfast=False, keepdb=False, **kwargs):
            self.verbosity = verbosity
            self.failfast = failfast
            self.keepdb = keepdb

        @classmethod
        def add_arguments(cls, parser):
            parser.add_argument(
                '--keepdb', action='store_true',
                help='Preserves the test DB between runs.'
            )

        def run_tests(self, test_labels, **kwargs):
            """Run pytest and return the exitcode.

            It translates some of Django's test command option to pytest's.
            """
            import pytest

            argv = []
            if self.verbosity == 0:
                argv.append('--quiet')
            if self.verbosity == 2:
                argv.append('--verbose')
            if self.verbosity == 3:
                argv.append('-vv')
            if self.failfast:
                argv.append('--exitfirst')
            if self.keepdb:
                argv.append('--reuse-db')

            argv.extend(test_labels)
            return pytest.main(argv)

Add the path to this class in your Django settings:

.. code-block:: python

    TEST_RUNNER = 'my_project.runner.PytestTestRunner'

Usage:

.. code-block:: bash

    ./manage.py test <django args> -- <pytest args>

**Note**: the pytest-django command line options ``--ds`` and ``--dc`` are not
compatible with this approach, you need to use the standard Django methods of
setting the ``DJANGO_SETTINGS_MODULE``/``DJANGO_CONFIGURATION`` environment
variables or the ``--settings`` command line option.

How can I give database access to all my tests without the `django_db` marker?
------------------------------------------------------------------------------

Create an autouse fixture and put it in ``conftest.py`` in your project root:

.. code-block:: python

    @pytest.fixture(autouse=True)
    def enable_db_access_for_all_tests(db):
        pass

How/where can I get help with pytest/pytest-django?
---------------------------------------------------

Usage questions can be asked on StackOverflow with the `pytest tag`_.

If you think you've found a bug or something that is wrong in the
documentation, feel free to `open an issue on the GitHub project`_ for
pytest-django.

Direct help can be found in the #pytest IRC channel `on irc.libera.chat
<ircs://irc.libera.chat:6697/#pytest>`_ (using an IRC client, `via webchat
<https://web.libera.chat/#pytest>`_, or `via Matrix
<https://matrix.to/#/%23pytest:libera.chat>`_).

.. _pytest tag: https://stackoverflow.com/search?q=pytest
.. _open an issue on the GitHub project:
    https://github.com/pytest-dev/pytest-django/issues/
