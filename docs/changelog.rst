Changelog
=========

v3.10.0 (2020-08-25)
--------------------

Improvements
^^^^^^^^^^^^

* Officialy support Django 3.1

* Preliminary supoprt for upcoming Django 3.2

* Support for pytest-xdist 2.0


Misc
^^^^

* Fix running pytest-django's own tests against pytest 6.0 (#855)


v3.9.0 (2020-03-31)
-------------------

Improvements
^^^^^^^^^^^^

* Improve test ordering with Django test classes (#830)

* Remove import of pkg_resources for parsing pytest version (performance) (#826)

Bugfixes
^^^^^^^^

* Work around unittest issue with pytest 5.4.{0,1} (#825)

* Don't break --failed-first when re-ordering tests (#819, #820)

* pytest_addoption: use `group.addoption` (#833)

Misc
^^^^

* Remove Django version from --nomigrations heading (#822)

* docs: changelog: prefix headers with v for permalink anchors

* changelog: add custom/fixed anchor for last version

* setup.py: add Changelog to project_urls


v3.8.0 (2020-01-14)
--------------------

Improvements
^^^^^^^^^^^^

* Make Django's assertion helpers available in pytest_django.asserts (#709).

* Report django-configurations setting (#791)


v3.7.0 (2019-11-09)
-------------------

Bugfixes
^^^^^^^^

* Monkeypatch pytest to not use ``TestCase.debug`` with unittests, instead
  of patching it into Django (#782).

* Work around pytest crashing due to ``pytest.fail`` being used from within the
  DB blocker, and pytest trying to display an object representation involving
  DB access (#781).  pytest-django uses a ``RuntimeError`` now instead.


v3.6.0 (2019-10-17)
-------------------

Features
^^^^^^^^

* Rename test databases when running parallel Tox (#678, #680)

Bugfixes
^^^^^^^^

* Django unittests: restore "debug" function (#769, #771)

Misc
^^^^

* Improve/harden internal tests / infrastructure.


v3.5.1 (2019-06-29)
-------------------

Bugfixes
^^^^^^^^

* Fix compatibility with pytest 5.x (#751)

v3.5.0 (2019-06-03)
-------------------

Features
^^^^^^^^

* Run tests in the same order as Django (#223)

* Use verbosity=0 with disabled migrations (#729, #730)

Bugfixes
^^^^^^^^

* django_db_setup: warn instead of crash with teardown errors (#726)

Misc
^^^^
* tests: fix test_sqlite_database_renamed (#739, #741)

* tests/conftest.py: move import of db_helpers (#737)

* Cleanup/improve coverage, mainly with tests (#706)

* Slightly revisit unittest handling (#740)


v3.4.8 (2019-02-26)
-------------------

Bugfixes
^^^^^^^^

* Fix DB renaming fixture for Multi-DB environment with SQLite (#679)

v3.4.7 (2019-02-03)
-------------------

Bugfixes
^^^^^^^^

* Fix disabling/handling of unittest methods with pytest 4.2+ (#700)

v3.4.6 (2019-02-01)
-------------------

Bugfixes
^^^^^^^^

* django_find_project: add cwd as fallback always (#690)

Misc
^^^^

* Enable tests for Django 2.2 and add classifier (#693)
* Disallow pytest 4.2.0 in ``install_requires`` (#697)

v3.4.5 (2019-01-07)
-------------------

Bugfixes
^^^^^^^^

* Use ``request.config`` instead of ``pytest.config`` (#677)
* :fixture:`admin_user`: handle "email" username_field (#676)

Misc
^^^^

* Minor doc fixes (#674)
* tests: fix for pytest 4 (#675)

v3.4.4 (2018-11-13)
-------------------

Bugfixes
^^^^^^^^

* Refine the django.conf module check to see if the settings really are
  configured (#668).
* Avoid crash after OSError during Django path detection (#664).

Features
^^^^^^^^

* Add parameter info to fixture assert_num_queries to display additional message on failure (#663).

Docs
^^^^

* Improve doc for django_assert_num_queries/django_assert_max_num_queries.
* Add warning about sqlite specific snippet + fix typos (#666).

Misc
^^^^

* MANIFEST.in: include tests for downstream distros (#653).
* Ensure that the LICENSE file is included in wheels (#665).
* Run black on source.


v3.4.3 (2018-09-16)
-------------------

Bugfixes
^^^^^^^^

* Fix OSError with arguments containing ``::`` on Windows (#641).

v3.4.2 (2018-08-20)
-------------------

Bugfixes
^^^^^^^^

* Changed dependency for pathlib to pathlib2 (#636).
* Fixed code for inserting the project to sys.path with pathlib to use an
  absolute path, regression in 3.4.0 (#637, #638).

v3.4.0 (2018-08-16)
-------------------

Features
^^^^^^^^

* Added new fixture :fixture:`django_assert_max_num_queries` (#547).
* Added support for ``connection`` and returning the wrapped context manager
  with :fixture:`django_assert_num_queries` (#547).
* Added support for resetting sequences via
  :fixture:`django_db_reset_sequences` (#619).

Bugfixes
^^^^^^^^

* Made sure to not call django.setup() multiple times (#629, #531).

Compatibility
^^^^^^^^^^^^^

* Removed py dependency, use pathlib instead (#631).

v3.3.3 (2018-07-26)
-------------------

Bug fixes
^^^^^^^^^

* Fixed registration of :py:func:`~pytest.mark.ignore_template_errors` marker,
  which is required with ``pytest --strict`` (#609).
* Fixed another regression with unittest (#624, #625).

Docs
^^^^

* Use sphinx_rtf_theme (#621).
* Minor fixes.

v3.3.2 (2018-06-21)
-------------------

Bug fixes
^^^^^^^^^

* Fixed test for classmethod with Django TestCases again (#618,
  introduced in #598 (3.3.0)).

Compatibility
^^^^^^^^^^^^^

* Support Django 2.1 (no changes necessary) (#614).

v3.3.0 (2018-06-15)
-------------------

Features
^^^^^^^^

* Added new fixtures ``django_mail_dnsname`` and ``django_mail_patch_dns``,
  used by ``mailoutbox`` to monkeypatch the ``DNS_NAME`` used in
  :py:mod:`django.core.mail` to improve performance and
  reproducibility.

Bug fixes
^^^^^^^^^

* Fixed test for classmethod with Django TestCases (#597, #598).
* Fixed RemovedInPytest4Warning: MarkInfo objects are deprecated (#596, #603)
* Fixed scope of overridden settings with live_server fixture: previously they
  were visible to following tests (#612).

Compatibility
^^^^^^^^^^^^^

* The required `pytest` version changed from >=2.9 to >=3.6.

v3.2.1
------

* Fixed automatic deployment to PyPI.

v3.2.0
------

Features
^^^^^^^^

* Added new fixture `django_assert_num_queries` for testing the number of
  database queries (#387).
* `--fail-on-template-vars` has been improved and should now return
  full/absolute path (#470).
* Support for setting the live server port (#500).
* unittest: help with setUpClass not being a classmethod (#544).

Bug fixes
^^^^^^^^^

* Fix --reuse-db and --create-db not working together (#411).
* Numerous fixes in the documentation. These should not go unnoticed 🌟

Compatibility
^^^^^^^^^^^^^

* Support for Django 2.0 has been added.
* Support for Django before 1.8 has been dropped.

v3.1.2
------

Bug fixes
^^^^^^^^^

* Auto clearing of ``mail.outbox`` has been re-introduced to not break
  functionality in 3.x.x release. This means that Compatibility issues
  mentioned in the 3.1.0 release are no longer present. Related issue:
  `pytest-django issue <https://github.com/pytest-dev/pytest-django/issues/433>`__

v3.1.1
------

Bug fixes
^^^^^^^^^

* Workaround `--pdb` interaction with Django TestCase. The issue is caused by
  Django TestCase not implementing TestCase.debug() properly but was brought to
  attention with recent changes in pytest 3.0.2. Related issues:
  `pytest issue <https://github.com/pytest-dev/pytest/issues/1977>`__,
  `Django issue <https://code.djangoproject.com/ticket/27391>`__

v3.1.0
------

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


v3.0.0
------

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
  will need to mark them with the ``pytest.mark.django_db`` marker or
  request the ``db`` fixture.

* The previously undocumented internal fixtures ``_django_db_setup``,
  ``_django_cursor_wrapper`` have been removed in favour of the new public
  fixtures. If you previously relied on these internal fixtures, you must
  update your code. See :ref:`advanced-database-configuration` for more
  information on the new fixtures and example use cases.

v2.9.1
------

Bug fixes
^^^^^^^^^

* Fix regression introduced in 2.9.0 that caused TestCase subclasses with
  mixins to cause errors. Thanks MikeVL for `the bug report
  <https://github.com/pytest-dev/pytest-django/issues/280>`__.


v2.9.0
------

v2.9.0 focus on compatibility with Django 1.9 and master as well as pytest 2.8.1
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

v2.8.0
------

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

v2.7.0
------

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

v2.6.2
------

* Fixed a bug that caused doctests to runs. Thanks to @jjmurre for the patch

* Fixed issue #88 - make sure to use SQLite in memory database when running
  with pytest-xdist.

v2.6.1
------
This is a bugfix/support release with no new features:

* Added support for Django 1.7 beta and Django master as of 2014-04-16.
  pytest-django is now automatically tested against the latest git master
  version of Django.

* Support for MySQL with MyISAM tables. Thanks to Zach Kanzler and Julen Ruiz
  Aizpuru for fixing this. This fixes issue #8 #64.

v2.6.0
------
* Experimental support for Django 1.7 / Django master as of 2014-01-19.

  pytest-django is now automatically tested against the latest git version of
  Django. The support is experimental since Django 1.7 is not yet released, but
  the goal is to always be up to date with the latest Django master

v2.5.1
------
Invalid release accidentally pushed to PyPI (identical to 2.6.1). Should not be
used - use 2.6.1 or newer to avoid confusion.


v2.5.0
------
* Python 2.5 compatibility dropped. py.test 2.5 dropped support for Python 2.5,
  therefore it will be hard to properly support in pytest-django. The same
  strategy as for pytest itself is used: No code will be changed to prevent
  Python 2.5 from working, but it will not be actively tested.

* pytest-xdist support: it is now possible to run tests in parallel. Just use
  pytest-xdist as normal (pass -n to py.test). One database will be created for
  each subprocess so that tests run independent from each other.

v2.4.0
------
* Support for py.test 2.4 pytest_load_initial_conftests. This makes it possible
  to import Django models in project conftest.py files, since pytest-django
  will be initialized before the conftest.py is loaded.

v2.3.1
------
* Support for Django 1.5 custom user models, thanks to Leonardo Santagada.


v2.3.0
------

* Support for configuring settings via django-configurations. Big thanks to
  Donald Stufft for this feature!

v2.2.1
------

* Fixed an issue with the settings fixture when used in combination with
  django-appconf. It now uses pytest's monkeypatch internally and should
  be more robust.

v2.2.0
------

* Python 3 support. pytest-django now supports Python 3.2 and 3.3 in addition
  to 2.5-2.7. Big thanks to Rafal Stozek for making this happen!

v2.1.0
------

* Django 1.5 support. pytest-django is now tested against 1.5 for Python
  2.6-2.7. This is the first step towards Python 3 support.

v2.0.1
------

* Fixed #24/#25: Make it possible to configure Django via
  ``django.conf.settings.configure()``.

* Fixed #26: Don't set DEBUG_PROPAGATE_EXCEPTIONS = True for test runs. Django
  does not change this setting in the default test runner, so pytest-django
  should not do it either.

v2.0.0
------

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

v1.4
----
* Removed undocumented pytest.load_fixture: If you need this feature, just use
  ``django.management.call_command('loaddata', 'foo.json')`` instead.
* Fixed issue with RequestFactory in Django 1.3.

* Fixed issue with RequestFactory in Django 1.3.

v1.3
----
* Added ``--reuse-db`` and ``--create-db`` to allow database re-use. Many
  thanks to `django-nose <https://github.com/jbalogh/django-nose>`__ for
  code and inspiration for this feature.

v1.2.2
------
* Fixed Django 1.3 compatibility.

v1.2.1
------
* Disable database access and raise errors when using --no-db and accessing
  the database by accident.

v1.2
----
* Added the ``--no-db`` command line option.

v1.1.1
------
* Flush tables after each test run with transaction_test_case instead of before.

v1.1
----

* The initial release of this fork from `Ben Firshman original project
  <http://github.com/bfirsh/pytest_django>`__
* Added documentation
* Uploaded to PyPI for easy installation
* Added the ``transaction_test_case`` decorator for tests that needs real transactions
* Added initial implementation for live server support via a funcarg (no docs yet, it might change!)
