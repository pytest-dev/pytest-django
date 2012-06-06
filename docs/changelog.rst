Changelog
=========

1.3
---
 * Added ``--reuse-db`` and ``--create-db`` to allow database re-use. Many
   thanks to `django-nose` <https://github.com/jbalogh/django-nose>` for
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
