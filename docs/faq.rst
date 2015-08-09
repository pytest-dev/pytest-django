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

How can I make sure that all my tests run with a specific locale?
-----------------------------------------------------------------

Create a `pytest fixture <http://pytest.org/latest/fixture.html>`_ that is
automatically run before each test case. To run all tests with the english
locale, put the following code in your project's `conftest.py
<http://pytest.org/latest/plugins.html>`_ file::

    from django.utils.translation import activate

    @pytest.fixture(autouse=True)
    def set_default_language():
        activate('en')

.. _faq-tests-not-being-picked-up:

My tests are not being found. Why not?
-------------------------------------------------------------------------------------
 By default, py.test looks for tests in files named ``test_*.py`` (note that
 this is not the same as ``test*.py``).  If you have your tests in files with
 other names, they will not be collected. It is common to put tests under
 ``app_directory/tests/views.py``. To find those tests, create a ``pytest.ini``
 file in your project root with the contents::

    [pytest]
    python_files=*.py

When debugging test collection problems, the ``--collectonly`` flag and ``-rs``
(report skipped tests) can be helpful.

How do South and pytest-django play together?
---------------------------------------------

pytest-django detects South and applies its monkey-patch, which gets fixed
to handle initial data properly (which South would skip otherwise, because
of a bug).

The ``SOUTH_TESTS_MIGRATE`` Django setting can be used to control whether
migrations are used to construct the test database.

Does pytest-django work with the pytest-xdist plugin?
-----------------------------------------------------

Yes. pytest-django supports running tests in parallel with pytest-xdist. Each
process created by xdist gets its own separate database that is used for the
tests. This ensures that each test can run independently, regardless of wheter
transactions are tested or not.

.. _faq-getting-help:

How/where can I get help with pytest/pytest-django?
---------------------------------------------------

Usage questions can be asked on StackOverflow with the `pytest tag
<http://stackoverflow.com/search?q=pytest>`_.

If you think you've found a bug or something that is wrong in the
documentation, feel free to `open an issue on the Github project for
pytest-django <https://github.com/pytest-dev/pytest-django/issues/>`_.

Direct help can be found in the #pylib IRC channel on irc.freenode.org.
