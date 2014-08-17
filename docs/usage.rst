.. _usage:

Usage and invocations
=====================

Basic usage
-----------

When using pytest-django, django-admin.py or manage.py is not used to run
tests. This makes it possible to invoke py.test and other plugins with all its
different options directly.

Running a test suite is done by invoking the py.test command directly::

    py.test

Specific test files or directories can be selected by specifying the test file names directly on
the command line::

    py.test test_something.py a_directory

See the `py.test documentation on Usage and invocations
<http://pytest.org/latest/usage.html>`_ for more help on available parameters.

Running tests in parallel with pytest-xdist
-------------------------------------------
pytest-django supports running tests on multiple processes to speed up test
suite run time. This can lead to significant speed improvements on multi
core/multi CPU machines.

This requires the pytest-xdist plugin to be available, it can usually be
installed with::

    pip install pytest-xdist

You can then run the tests by running::

    py.test -n <number of processes>

When tests are invoked with xdist, pytest-django will create a separate test
database for each process. Each test database will be given a suffix
(something like "gw0", "gw1") to map to a xdist process. If your database name
is set to "foo", the test database with xdist will be "test_foo_gw0",
"test_foo_gw1" etc.

See the full documentation on `pytest-xdist
<http://pytest.org/latest/xdist.html>`_ for more information. Among other
features, pytest-xdist can distribute/coordinate test execution on remote
machines.
