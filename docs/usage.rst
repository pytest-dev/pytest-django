.. _usage:

Usage and invocations
=====================

Basic usage
-----------

When using pytest-django, django-admin.py or manage.py is not used to run
tests. This makes it possible to invoke pytest and other plugins with all its
different options directly.

Running a test suite is done by invoking the pytest command directly::

    pytest

Specific test files or directories can be selected by specifying the test file names directly on
the command line::

    pytest test_something.py a_directory

See the `pytest documentation on Usage and invocations
<https://pytest.org/en/stable/usage.html>`_ for more help on available parameters.

Additional command line options
-------------------------------

``--fail-on-template-vars`` - fail for invalid variables in templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Fail tests that render templates which make use of invalid template variables.

You can switch it on in `pytest.ini`::

    [pytest]
    FAIL_INVALID_TEMPLATE_VARS = True
    
Additional pytest.ini settings
------------------------------

``django_debug_mode`` - change how DEBUG is set
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default tests run with the
`DEBUG <https://docs.djangoproject.com/en/stable/ref/settings/#debug>`_
setting set to ``False``. This is to ensure that the observed output of your
code matches what will be seen in a production setting.

If you want ``DEBUG`` to be set::

    [pytest]
    django_debug_mode = true

You can also use ``django_debug_mode = keep`` to disable the overriding and use
whatever is already set in the Django settings.

Running tests in parallel with pytest-xdist
-------------------------------------------
pytest-django supports running tests on multiple processes to speed up test
suite run time. This can lead to significant speed improvements on multi
core/multi CPU machines.

This requires the pytest-xdist plugin to be available, it can usually be
installed with::

    pip install pytest-xdist

You can then run the tests by running::

    pytest -n <number of processes>

When tests are invoked with xdist, pytest-django will create a separate test
database for each process. Each test database will be given a suffix
(something like "gw0", "gw1") to map to a xdist process. If your database name
is set to "foo", the test database with xdist will be "test_foo_gw0",
"test_foo_gw1" etc.

See the full documentation on `pytest-xdist
<https://github.com/pytest-dev/pytest-xdist/blob/master/README.rst>`_ for more
information. Among other features, pytest-xdist can distribute/coordinate test
execution on remote machines.
