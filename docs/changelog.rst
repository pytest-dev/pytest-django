Changelog
=========
2.6.0
-----
* Experimental support for Django 1.7 / Django master as of 2014-01-19.

  pytest-django is now automatically tested against the latest git version of
  Django. The support is experimental since Django 1.7 is not yet released, but
  the goal is to always be up to date with the latest Django master

2.5.0
-----
* Python 2.5 compatibility dropped. py.test 2.5 dropped support for Python 2.5,
  therefore it will be hard to properly support in pytest-django. The same
  strategy as for pytest itself is used: No code will be changed to prevent
  Python 2.5 from working, but it will not be actively tested.

* pytest-xdist support: it is now possible to run tests in parallell. Just use
  pytest-xdist as normal (pass -n to py.test). One database will be created for
  each subprocess so that tests run independent from eachother.

2.4.0
-----
* Support for py.test 2.4 pytest_load_initial_conftests. This makes it possible
  to import Django models in project conftest.py files, since pytest-django
  will be initialized before the conftest.py is loaded.

2.3.1
-----
* Support for Django 1.5 custom user models, thanks to Leonardo Santagada.


2.3.0
-----

* Support for configuring settings via django-configurations. Big thanks to
  Donald Stufft for this feature!

2.2.1
-----

* Fixed an issue with the settings fixture when used in combination with
  django-appconf. It now uses pytest's monkeypatch internally and should
  be more robust.

2.2.0
-----

* Python 3 support. pytest-django now supports Python 3.2 and 3.3 in addition
  to 2.5-2.7. Big thanks to Rafal Stozek for making this happend!

2.1.0
-----

* Django 1.5 support. pytest-django is now tested against 1.5 for Python
  2.6-2.7. This is the first step towards Python 3 support.

2.0.1
-----

* Fixed #24/#25: Make it possible to configure Django via
  ``django.conf.settings.configure()``.

* Fixed #26: Don't set DEBUG_PROPAGATE_EXCEPTIONS = True for test runs. Django
  does not change this setting in the default test runner, so pytest-django
  should not do it either.

2.0.0
-----

This release is *backward incompatible*. The biggest change is the need
to add the ``pytest.mark.django_db`` to tests which needs database
access.

Finding such tests is generally very easy: just run your test suite, the
tests which needs database access will fail. Add ``pytestmark =
pytest.mark.django_db`` to the module/class or decorate them with
``@pytest.mark.django_db``.

Most of the interals has been rewritten, exploiting py.test's new
fixtures API. This release would not be possible without Floris
Bruynooghe who did the port to the new fixture API and fixed a number of
bugs.

The tests for pytest-django itself has been greatly improved, paving the
way for easier additions of new and exciting features in the future!

* Semantic version numbers will now be used for releases, see http://semver.org/.

* Do not allow database access in tests by default.  Introduce
  ``pytest.mark.django_db`` to enable database access.

* Large parts re-written using py.test's 2.3 fixtures API (issue #9).

  - Fixes issue #17: Database changes made in fixtures or funcargs
    will now be reverted as well.

  - Fixes issue 21: Database teardown errors are no longer hidden.

  - Fixes issue 16: Database setup and teardown for non-TestCase
    classes works correctly.

* ``pytest.urls()`` is replaced by the standard marking API and is now
  used as ``pytest.mark.urls()``

* Make the plugin behave gracefully without DJANGO_SETTINGS_MODULE
  specified.  ``py.test`` will still work and tests needing django
  features will skip (issue #3).

* Allow specifying of ``DJANGO_SETTINGS_MODULE`` on the command line
  (``--ds=settings``) and py.test ini configuration file as well as the
  environment variable (issue #3).

* Deprecate the ``transaction_test_case`` decorator, this is now
  integrated with the ``django_db`` mark.

1.4
---
* Removed undocumented pytest.load_fixture: If you need this feature, just use
  ``django.management.call_command('loaddata', 'foo.json')`` instead.
* Fixed issue with RequestFactory in Django 1.3.

* Fixed issue with RequestFactory in Django 1.3.

1.3
---
* Added ``--reuse-db`` and ``--create-db`` to allow database re-use. Many
  thanks to `django-nose <https://github.com/jbalogh/django-nose>`_ for
  code and inspiration for this feature.

1.2.2
-----
* Fixed Django 1.3 compatibility.

1.2.1
-----
* Disable database access and raise errors when using --no-db and accessing
  the database by accident.

1.2
---
* Added the ``--no-db`` command line option.

1.1.1
-----
* Flush tables after each test run with transaction_test_case instead of before.

1.1
---

* The initial release of this fork from `Ben Firshman original project <http://github.com/bfirsh/pytest_django>`_
* Added documentation
* Uploaded to PyPI for easy installation
* Added the ``transaction_test_case`` decorator for tests that needs real transactions
* Added initial implemantion for live server support via a funcarg (no docs yet, it might change!)
