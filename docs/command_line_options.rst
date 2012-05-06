Command line options
=====================

``--no-db``
-----------
Does not create a test database. ``--no-db`` is useful to only run tests which
does not need access to a database. This can be a big time saver when if you
have a lot of tables that needs to be created if you just want to run a couple
of unittests.
