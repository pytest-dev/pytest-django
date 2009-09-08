pytest_django
=============

pytest_django is a plugin for [py.test](http://pytest.org/) that provides a set of useful tools for testing [Django](http://www.djangoproject.com/) applications.

Requires:

  * Django 1.1
  * py.test 1.0.0

Installation
------------

    $ python setup.py install

Then simply create a `conftest.py` file in the root of your Django project 
containing:

    pytest_plugins = ['django']

Usage
-----

Run py.test in the root directory of your Django project:

    $ py.test

This will attempt to import the Django settings and run any tests.

Note that the default py.test collector is used, as well as any file within a 
tests directory. As such, so it will not honour `INSTALLED_APPS`. You must use 
`collect_ignore` in a `conftest.py` file to exclude any tests you don't want 
to be run.

See [py.test's documentation](http://pytest.org/) for more information, 
including usage of the `-k` option for selecting specific tests.

A `--settings` option is provided for explicitly setting a settings module, 
similar to `manage.py`.

pytest_django makes py.test's built in unittest support fully backwards 
compatible with Django's unittest test cases. If they are failing, this is a 
bug.

Hooks
-----

The session start/finish and setup/teardown hooks act like Django's `test` 
management command and unittest test cases. This includes creating the test 
database and maintaining a constant test environment, amongst other things. 
Additionally, it will attempt to restore the settings at the end of each test, 
so it is safe to modify settings within a test.

Funcargs
--------

### `client`

A Django test client instance.

Example:

    def test_something(client)
        assert 'Success!' in client.get('/path/')
        

### `rf`

An instance of Simon Willison's excellent 
[RequestFactory](http://www.djangosnippets.org/snippets/963/).

`@py.test.params` decorator
---------------------------

A decorator to make parametrised tests easy. Takes a list of dictionaries of 
keyword arguments for the function. A test is created for each dictionary.

Example:

    @py.test.params([dict(a=1, b=2), dict(a=3, b=3), dict(a=5, b=4)])  
    def test_equals(a, b):
        assert a == b

Fixtures
--------

Fixtures can be loaded with `py.test.load_fixture(name)`. For example:

    def pytest_funcarg__articles(request):
        py.test.load_fixture('test_articles')
        return Article.objects.all()

