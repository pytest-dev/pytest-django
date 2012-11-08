"""Functions to aid in preserving the test database between test runs.

The code in this module is heavily inspired by django-nose:
https://github.com/jbalogh/django-nose/
"""

import new
import py


def can_support_db_reuse(connection):
    """Return whether it makes any sense to use REUSE_DB with the backend of a connection."""
    # This is a SQLite in-memory DB. Those are created implicitly when
    # you try to connect to them, so our test below doesn't work.
    return connection.creation._get_test_db_name() != ':memory:'


def test_database_exists_from_previous_run(connection):
    # Check for sqlite memory databases
    if not can_support_db_reuse(connection):
        return False

    # Try to open a cursor to the test database
    orig_db_name = connection.settings_dict['NAME']
    connection.settings_dict['NAME'] = connection.creation._get_test_db_name()

    try:
        connection.cursor()
        return True
    except StandardError:  # TODO: Be more discerning but still DB agnostic.
        return False
    finally:
        connection.close()
        connection.settings_dict['NAME'] = orig_db_name


def create_test_db(self, verbosity=1, autoclobber=False):
    """
    This method is a monkey patched version of create_test_db that
    will not actually create a new database, but just reuse the
    existing.
    """
    test_database_name = self._get_test_db_name()
    self.connection.settings_dict['NAME'] = test_database_name

    if verbosity >= 1:
        test_db_repr = ''
        if verbosity >= 2:
            test_db_repr = " ('%s')" % test_database_name
        print "Re-using existing test database for alias '%s'%s..." % (
            self.connection.alias, test_db_repr)

    self.connection.features.confirm()

    return test_database_name


def monkey_patch_creation_for_db_reuse():
    from django.db import connections

    for alias in connections:
        connection = connections[alias]
        creation = connection.creation

        if test_database_exists_from_previous_run(connection):
            # Make sure our monkey patch is still valid in the future
            assert hasattr(creation, 'create_test_db')

            creation.create_test_db = new.instancemethod(
                    create_test_db, creation, creation.__class__)
