.. _managing_python_path:

Managing the Python path
========================

pytest needs to be able to import the code in your project. Normally, when
interacting with Django code, the interaction happens via ``manage.py``, which
will implicilty add that directory to the Python path.

However, when Python is started via the ``pytest`` command, some extra care is
needed to have the Python path setup properly. There are two ways to handle
this problem, described below.

Automatic looking for of Django projects
----------------------------------------

By default, pytest-django tries to find Django projects by automatically
looking for the project's ``manage.py`` file and adding its directory to the
Python path.

Looking for the ``manage.py`` file uses the same algorithm as pytest uses to
find ``pytest.ini``, ``tox.ini`` and ``setup.cfg``: Each test root directories
parents will be searched for ``manage.py`` files, and it will stop when the
first file is found.

If you have a custom project setup, have none or multiple ``manage.py`` files
in your project, the automatic detection may not be correct. See
:ref:`managing_the_python_path_explicitly` for more details on how to configure
your environment in that case.

.. _managing_the_python_path_explicitly:

Managing the Python path explicitly
-----------------------------------

First, disable the automatic Django project finder. Add this to
``pytest.ini``, ``setup.cfg`` or ``tox.ini``::

    [pytest]
    django_find_project = false


Next, you need to make sure that your project code is available on the Python
path. There are multiple ways to achieve this:

Managing your project with virtualenv, pip and editable mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to have your code available on the Python path when using
virtualenv and pip is to have a setup.py file and install your project in
editable mode when developing.

If you don't already have a setup.py file, creating a setup.py file with this
content will get you started::

    import setuptools
    setuptools.setup(name='myproj', version='1.0')

This ``setup.py`` file is not sufficient to distribute your package to PyPI or
more general packaging, but it should help you get started. Please refer to the
`Python Packaging User Guide
<https://python-packaging-user-guide.readthedocs.io/en/latest/tutorial.html#creating-your-own-project>`_
for more information on packaging Python applications.`

To install the project afterwards::

    pip install --editable .

Your code should then be importable from any Python application. You can also
add this directly to your project's requirements.txt file like this::

    # requirements.txt
    -e .
    django>=1.11
    pytest-django


Using pytest-pythonpath
~~~~~~~~~~~~~~~~~~~~~~~

You can also use the `pytest-pythonpath
<https://pypi.python.org/pypi/pytest-pythonpath>`_ plugin to explicitly add paths to
the Python path.
