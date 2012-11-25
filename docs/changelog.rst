Changelog
=========

1.5
---
* Large parts re-written using py.test's 2.3 fixtures API.

  - Fixes issue #17: Database changes made in fixtures or funcargs
    will now be reverted as well.

  - Fixes issue 21: Database teardown errors are no longer hidden.

1.4
---
* Removed undocumented pytest.load_fixture: If you need this feature, just use
  ``django.management.call_command('loaddata', 'foo.json')`` instead.

* Make the plugin behave gracefully without DJANGO_SETTINGS_MODULE
  specified.  ``py.test`` will still work and tests needing django
  features will skip.

* Allow specifying of DJANGO_SETTINGS_MODULE on the command line and
  py.test ini configuration file as well as the environment variable.

* Do not allow database access in tests by default.  Introduce
  ``pytest.mark.djangodb`` to enable database access.

* Deprecate the ``transaction_test_case`` decorator, this is now
  integrated with the ``djangodb`` mark.

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
