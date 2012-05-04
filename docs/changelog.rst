Changelog
=========

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
