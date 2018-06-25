#############################
Contributing to pytest-django
#############################

Like every open-source project, pytest-django is always looking for motivated
individuals to contribute to its source code.  However, to ensure the highest
code quality and keep the repository nice and tidy, everybody has to follow a
few rules (nothing major, I promise :) )


*********
Community
*********

The fastest way to get feedback on contributions/bugs is usually to open an
issue in the `issue tracker`_.

Discussions also happen via IRC in #pylib on irc.freenode.org. You may also
be interested in following `@andreaspelme`_ on Twitter.

*************
In a nutshell
*************

Here's what the contribution process looks like, in a bullet-points fashion:

#. pytest-django is hosted on `GitHub`_, at
   https://github.com/pytest-dev/pytest-django
#. The best method to contribute back is to create an account there and fork
   the project. You can use this fork as if it was your own project, and should
   push your changes to it.
#. When you feel your code is good enough for inclusion, "send us a `pull
   request`_", by using the nice GitHub web interface.


*****************
Contributing Code
*****************


Getting the source code
=======================

- Code will be reviewed and tested by at least one core developer, preferably
  by several. Other community members are welcome to give feedback.
- Code *must* be tested. Your pull request should include unit-tests (that
  cover the piece of code you're submitting, obviously).
- Documentation should reflect your changes if relevant. There is nothing worse
  than invalid documentation.
- Usually, if unit tests are written, pass, and your change is relevant, then
  your pull request will be merged.

Since we're hosted on GitHub, pytest-django uses `git`_ as a version control
system.

The `GitHub help`_ is very well written and will get you started on using git
and GitHub in a jiffy. It is an invaluable resource for newbies and oldtimers
alike.


Syntax and conventions
======================

We try to conform to `PEP8`_ as much as possible. A few highlights:

- Indentation should be exactly 4 spaces. Not 2, not 6, not 8. **4**. Also,
  tabs are evil.
- We try (loosely) to keep the line length at 79 characters. Generally the rule
  is "it should look good in a terminal-based editor" (eg vim), but we try not
  be [Godwin's law] about it.


Process
=======

This is how you fix a bug or add a feature:

#. `fork`_ the repository on GitHub.
#. Checkout your fork.
#. Hack hack hack, test test test, commit commit commit, test again.
#. Push to your fork.
#. Open a pull request.


Tests
=====

Having a wide and comprehensive library of unit-tests and integration tests is
of exceeding importance. Contributing tests is widely regarded as a very
prestigious contribution (you're making everybody's future work much easier by
doing so). Good karma for you. Cookie points. Maybe even a beer if we meet in
person :)

Generally tests should be:

- Unitary (as much as possible). I.E. should test as much as possible only on
  one function/method/class. That's the very definition of unit tests.
  Integration tests are also interesting obviously, but require more time to
  maintain since they have a higher probability of breaking.
- Short running. No hard numbers here, but if your one test doubles the time it
  takes for everybody to run them, it's probably an indication that you're
  doing it wrong.

In a similar way to code, pull requests will be reviewed before pulling
(obviously), and we encourage discussion via code review (everybody learns
something this way) or in the IRC channel.

Running the tests
-----------------

There is a Makefile in the repository which aids in setting up a virtualenv
and running the tests::

    $ make test

You can manually create the virtualenv using::

    $ make testenv

This will install a virtualenv with pytest and the latest stable version of
Django. The virtualenv can then be activated with::

    $ source bin/activate

Then, simply invoke pytest to run the test suite::

    $ pytest --ds=pytest_django_test.settings_sqlite


tox can be used to run the test suite under different configurations by
invoking::

    $ tox

There is a huge number of unique test configurations (98 at the time of
writing), running them all will take a long time. All valid configurations can
be found in `tox.ini`. To test against a few of them, invoke tox with the `-e`
flag::

    $ tox -e py36-dj111-postgres,py27-dj111-mysql_innodb

This will run the tests on Python 3.6/Django 1.11/PostgeSQL and Python
2.7/Django 1.11/MySQL.


Measuring test coverage
-----------------------

Some of the tests are executed in subprocesses. Because of that regular
coverage measurements (using pytest-cov plugin) are not reliable.

If you want to measure coverage you'll need to create .pth file as described in
`subprocess section of coverage documentation`_. If you're using
``setup.py develop`` you should uninstall pytest_django (using pip)
for the time of measuring coverage.

You'll also need mysql and postgres databases. There are predefined settings
for each database in the tests directory. You may want to modify these files
but please don't include them in your pull requests.

After this short initial setup you're ready to run tests::

    $ COVERAGE_PROCESS_START=`pwd`/.coveragerc COVERAGE_FILE=`pwd`/.coverage PYTHONPATH=`pwd` pytest --ds=pytest_django_test.settings_postgres

You should repeat the above step for sqlite and mysql before the next step.
This step will create a lot of ``.coverage`` files with additional suffixes for
every process.

The final step is to combine all the files created by different processes and
generate the html coverage report::

    $ coverage combine
    $ coverage html

Your coverage report is now ready in the ``htmlcov`` directory.


Continuous integration
----------------------

`Travis`_ is used to automatically run all tests against all supported versions
of Python, Django and different database backends.

The `pytest-django Travis`_ page shows the latest test run. Travis will
automatically pick up pull requests, test them and report the result directly
in the pull request.

**************************
Contributing Documentation
**************************

Perhaps considered "boring" by hard-core coders, documentation is sometimes
even more important than code! This is what brings fresh blood to a project,
and serves as a reference for oldtimers. On top of this, documentation is the
one area where less technical people can help most - you just need to write a
semi-decent English. People need to understand you. We don't care about style
or correctness.

Documentation should be:

- We use `Sphinx`_/`restructuredText`_. So obviously this is the format you
  should use :) File extensions should be .rst.
- Written in English. We can discuss how it would bring more people to the
  project to have a Klingon translation or anything, but that's a problem we
  will ask ourselves when we already have a good documentation in English.
- Accessible. You should assume the reader to be moderately familiar with
  Python and Django, but not anything else. Link to documentation of libraries
  you use, for example, even if they are "obvious" to you (South is the first
  example that comes to mind - it's obvious to any Django programmer, but not
  to any newbie at all).
  A brief description of what it does is also welcome.

Pulling of documentation is pretty fast and painless. Usually somebody goes
over your text and merges it, since there are no "breaks" and that GitHub
parses rst files automagically it's really convenient to work with.

Also, contributing to the documentation will earn you great respect from the
core developers. You get good karma just like a test contributor, but you get
double cookie points. Seriously. You rock.


.. note::

  This very document is based on the contributing docs of the `django CMS`_
  project. Many thanks for allowing us to steal it!


.. _fork: https://github.com/pytest-dev/pytest-django
.. _issue tracker: https://github.com/pytest-dev/pytest-django/issues
.. _Sphinx: http://sphinx.pocoo.org/
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _GitHub : http://www.github.com
.. _GitHub help : http://help.github.com
.. _freenode : http://freenode.net/
.. _@andreaspelme : https://twitter.com/andreaspelme
.. _pull request : http://help.github.com/send-pull-requests/
.. _git : http://git-scm.com/
.. _restructuredText: http://docutils.sourceforge.net/docs/ref/rst/introduction.html
.. _django CMS: https://www.django-cms.org/
.. _Travis: https://travis-ci.org/
.. _pytest-django Travis: https://travis-ci.org/pytest-dev/pytest-django
.. _`subprocess section of coverage documentation`: http://nedbatchelder.com/code/coverage/subprocess.html
