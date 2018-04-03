Changelog
=========

3.2.0
-----

Features
^^^^^^^^
* Add support for serialized rollback in transactional tests.
  Thanks to Piotr Karkut for `the bug report
  <https://github.com/pytest-dev/pytest-django/issues/329>`_.

3.1.2
-----

Bug fixes
^^^^^^^^^

* Auto clearing of ``mail.outbox`` has been re-introduced to not break
  functionality in 3.x.x release. This means that Compatibility issues
  mentioned in the 3.1.0 release are no longer present. Related issue:
  `pytest-django issue <https://github.com/pytest-dev/pytest-django/issues/433>`__

3.1.1
-----

Bug fixes
^^^^^^^^^

* Workaround `--pdb` interaction with Django TestCase. The issue is caused by
  Django TestCase not implementing TestCase.debug() properly but was brought to
  attention with recent changes in pytest 3.0.2. Related issues:
  `pytest issue <https://github.com/pytest-dev/pytest/issues/1977>`__,
  `Django issue <https://code.djangoproject.com/ticket/27391>`__

3.1.0
-----

Features
^^^^^^^^
* Added new function scoped fixture ``mailoutbox`` that gives access to
  djangos ``mail.outbox``. The will clean/empty the ``mail.outbox`` to
  assure that no old mails are still in the outbox.
* If ``django.contrib.sites`` is in your INSTALLED_APPS, Site cache will
  be cleared for each test to avoid hitting the cache and cause wrong Site
  object to be returned by ``Site.objects.get_current()``.

Compatibility
^^^^^^^^^^^^^
* IMPORTANT: the internal autouse fixture _django_clear_outbox has been
  removed. If you have relied on this to get an empty outbox for your
  test, you should change tests to use the ``mailoutbox`` fixture instead.
  See documentation of ``mailoutbox`` fixture for usage. If you try to
  access mail.outbox directly, AssertionError will be raised. If you
  previously relied on the old behaviour and do not want to change your
  tests, put this in your project conftest.py::

    @pytest.fixture(autouse=True)
    def clear_outbox():
        from django.core import mail
        mail.outbox = []


3.0.0
-----

Bug fixes
^^^^^^^^^

* Fix error when Django happens to be imported before pytest-django runs.
  Thanks to Will Harris for `the bug report
  <https://github.com/pytest-dev/pytest-django/issues/289>`__.

Features
^^^^^^^^
* Added a new option ``--migrations`` to negate a default usage of
  ``--nomigrations``.

* The previously internal pytest-django fixture that handles database creation
  and setup has been refactored, refined and made a public API.

  This opens up more flexibility and advanced use cases to configure the test
  database in new ways.

  See :ref:`advanced-database-configuration` for more information on the new
  fixtures and example use cases.

Compatibility
^^^^^^^^^^^^^
* Official for the pytest 3.0.0 (2.9.2 release should work too, though). The
  documentation is updated to mention ``pytest`` instead of ``py.test``.

* Django versions 1.4, 1.5 and 1.6 is no longer supported. The supported
  versions are now 1.7 and forward. Django master is supported as of
  2016-08-21.

* pytest-django no longer supports Python 2.6.

* Specifying the ``DJANGO_TEST_LIVE_SERVER_ADDRESS`` environment variable is no
  longer supported. Use ``DJANGO_LIVE_TEST_SERVER_ADDRESS`` instead.

* Ensuring accidental database access is now stricter than before. Previously
  database access was prevented on the cursor level. To be safer and prevent
  more cases, it is now prevented at the connection level. If you previously
  had tests which interacted with the databases without a database cursor, you
  will need to mark them with the :func:`pytest.mark.django_db` marker or
  request the ``db`` fixture.

* The previously undocumented internal fixtures ``_django_db_setup``,
  ``_django_cursor_wrapper`` have been removed in favour of the new public
  fixtures. If you previously relied on these internal fixtures, you must
  update your code. See :ref:`advanced-database-configuration` for more
  information on the new fixtures and example use cases.

2.9.1
-----

Bug fixes
^^^^^^^^^

* Fix regression introduced in 2.9.0 that caused TestCase subclasses with
  mixins to cause errors. Thanks MikeVL for `the bug report
  <https://github.com/pytest-dev/pytest-django/issues/280>`__.


2.9.0
-----

2.9.0 focus on compatibility with Django 1.9 and master as well as pytest 2.8.1
and Python 3.5

Features
^^^^^^^^
* ``--fail-on-template-vars`` - fail tests for invalid variables in templates.
  Thanks to Johannes Hoppe for idea and implementation. Thanks Daniel Hahler
  for review and feedback.

Bug fixes
^^^^^^^^^
* Ensure urlconf is properly reset when using @pytest.mark.urls. Thanks to
  Sarah Bird, David Szotten, Daniel Hahler and Yannick PÉROUX for patch and
  discussions. Fixes `issue #183
  <https://github.com/pytest-dev/pytest-django/issues/183>`__.

* Call ``setUpClass()`` in Django ``TestCase`` properly when test class is
  inherited multiple places. Thanks to Benedikt Forchhammer for report and
  initial test case. Fixes `issue #265
  <https://github.com/pytest-dev/pytest-django/issues/265>`__.

Compatibility
^^^^^^^^^^^^^

* Settings defined in ``pytest.ini``/``tox.ini``/``setup.cfg`` used to override
  ``DJANGO_SETTINGS_MODULE`` defined in the environment. Previously the order was
  undocumented. Now, instead the settings from the environment will be used
  instead. If you previously relied on overriding the environment variable,
  you can instead specify ``addopts = --ds=yourtestsettings`` in the ini-file
  which will use the test settings. See `PR #199
  <https://github.com/pytest-dev/pytest-django/pull/199>`__.

* Support for Django 1.9.

* Support for Django master (to be 1.10) as of 2015-10-06.

* Drop support for Django 1.3. While pytest-django supports a wide range of
  Django versions, extended for Django 1.3 was dropped in february 2013.

2.8.0
-----

Features
^^^^^^^^

* pytest's verbosity is being used for Django's code to setup/teardown the test
  database (#172).

* Added a new option `--nomigrations` to avoid running Django 1.7+ migrations
  when constructing the test database. Huge thanks to Renan Ivo for complete
  patch, tests and documentation.

Bug fixes
^^^^^^^^^

* Fixed compatibility issues related to Django 1.8's
  `setUpClass`/`setUpTestData`. Django 1.8 is now a fully supported version.
  Django master as of 2014-01-18 (the Django 1.9 branch) is also supported.

2.7.0
-----

Features
^^^^^^^^

* New fixtures: ``admin_user``, ``django_user_model`` and
  ``django_username_field`` (#109).

* Automatic discovery of Django projects to make it easier for new users. This
  change is slightly backward incompatible, if you encounter problems with it,
  the old behaviour can be restored by adding this to ``pytest.ini``,
  ``setup.cfg`` or ``tox.ini``:

  .. code-block:: ini

    [pytest]
    django_find_project = false

  Please see the :ref:`managing_python_path` section for more information.

Bugfixes
^^^^^^^^

* Fix interaction between ``db`` and ``transaction_db`` fixtures (#126).

* Fix admin client with custom user models (#124). Big thanks to Benjamin
  Hedrich and Dmitry Dygalo for patch and tests.

* Fix usage of South migrations, which were unconditionally disabled previously
  (#22).

* Fixed #119, #134: Call ``django.setup()`` in Django >=1.7 directly after
  settings is loaded to ensure proper loading of Django applications. Thanks to
  Ionel Cristian Mărieș, Daniel Hahler, Tymur Maryokhin, Kirill SIbirev, Paul
  Collins, Aymeric Augustin, Jannis Leidel, Baptiste Mispelon and Anatoly
  Bubenkoff for report, discussion and feedback.

* `The `live_server`` fixture can now serve static files also for Django>=1.7
  if the ``django.contrib.staticfiles`` app is installed. (#140).

* ``DJANGO_LIVE_TEST_SERVER_ADDRESS`` environment variable is read instead
  of ``DJANGO_TEST_LIVE_SERVER_ADDRESS``. (#140)

2.6.2
-----

* Fixed a bug that caused doctests to runs. Thanks to @jjmurre for the patch

* Fixed issue #88 - make sure to use SQLite in memory database when running
  with pytest-xdist.

2.6.1
-----
This is a bugfix/support release with no new features:

* Added support for Django 1.7 beta and Django master as of 2014-04-16.
  pytest-django is now automatically tested against the latest git master
  version of Django.

* Support for MySQL with MyISAM tables. Thanks to Zach Kanzler and Julen Ruiz
  Aizpuru for fixing this. This fixes issue #8 #64.

2.6.0
-----
* Experimental support for Django 1.7 / Django master as of 2014-01-19.

  pytest-django is now automatically tested against the latest git version of
  Django. The support is experimental since Django 1.7 is not yet released, but
  the goal is to always be up to date with the latest Django master

2.5.1
-----
Invalid release accidentally pushed to PyPI (identical to 2.6.1). Should not be
used - use 2.6.1 or newer to avoid confusion.


2.5.0
-----
* Python 2.5 compatibility dropped. py.test 2.5 dropped support for Python 2.5,
  therefore it will be hard to properly support in pytest-django. The same
  strategy as for pytest itself is used: No code will be changed to prevent
  Python 2.5 from working, but it will not be actively tested.

* pytest-xdist support: it is now possible to run tests in parallel. Just use
  pytest-xdist as normal (pass -n to py.test). One database will be created for
  each subprocess so that tests run independent from each other.

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
  to 2.5-2.7. Big thanks to Rafal Stozek for making this happen!

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
to add the ``pytest.mark.django_db`` to tests which require database
access.

Finding such tests is generally very easy: just run your test suite, the
tests which need database access will fail. Add ``pytestmark =
pytest.mark.django_db`` to the module/class or decorate them with
``@pytest.mark.django_db``.

Most of the internals have been rewritten, exploiting py.test's new
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
  thanks to `django-nose <https://github.com/jbalogh/django-nose>`__ for
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

* The initial release of this fork from `Ben Firshman original project
  <http://github.com/bfirsh/pytest_django>`__
* Added documentation
* Uploaded to PyPI for easy installation
* Added the ``transaction_test_case`` decorator for tests that needs real transactions
* Added initial implementation for live server support via a funcarg (no docs yet, it might change!)
