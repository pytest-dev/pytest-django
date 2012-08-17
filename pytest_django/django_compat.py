# Note that all functions here assume django is available.  So ensure
# this is the case before you call them.

from .live_server_helper import has_live_server_support


def disable_south_syncdb():
    """
    Make sure the builtin syncdb is used instead of South's.
    """
    from django.core import management
    commands = management.get_commands()

    if commands['syncdb'] == 'south':
        management._commands['syncdb'] = 'django.core'


def setup_databases(session):
    """Ensure test databases are set up for this session

    It is safe to call this multiple times.
    """
    if not hasattr(session, 'django_dbcfg'):
        disable_south_syncdb()
        dbcfg = session.django_runner.setup_databases()
        session.django_dbcfg = dbcfg


def teardown_databases(session):
    """Ensure test databases are torn down for this session

    It is safe to call this even if the databases where not setup in
    the first place.
    """
    if hasattr(session, 'django_runner') and hasattr(session, 'django_dbcfg'):
        print('\n')
        session.django_runner.teardown_databases(session.django_dbcfg)


def is_transaction_test_case(item):
    mark = getattr(item.obj, 'django_db', None)
    if mark:
        if getattr(mark, 'transaction', None):
            return True
        if has_live_server_support() and 'live_server' in item.funcargs:
            # This case is odd, it can only happen if someone marked
            # the function requesting live_server with the django_db
            # mark, but forgot to add transaction=True.
            return True


def is_django_unittest(item):
    """Returns True if the item is a Django test case, otherwise False"""
    try:
        from django.test import SimpleTestCase as TestCase
        TestCase  # Silence pyflakes
    except ImportError:
        from django.test import TestCase

    return (hasattr(item.obj, 'im_class') and
            issubclass(item.obj.im_class, TestCase))


def clear_django_outbox():
    """Clear any items in the Django test outbox"""
    from django.core import mail
    mail.outbox = []


def django_setup_item(item):
    """Setup Django databases for this test item

    Note that this should not be called for an item which does not need
    the Django database.
    """
    from django.test import TestCase

    if is_django_unittest(item) or is_transaction_test_case(item):
        pass
    else:
        item.django_unittest = TestCase(methodName='__init__')
        if item.obj.django_db.multidb:
            item.django_unittest.multi_db = True
        item.django_unittest._pre_setup()


def django_teardown_item(item):
    """Teardown Django databases for this test item

    Note that this should not be called for an item which does not
    need the Django database.
    """
    from django.db import connections
    from django.core.management import call_command

    if is_django_unittest(item):
        pass
    elif is_transaction_test_case(item):
        # Flush the database and close database connections
        # Django does this by default *before* each test instead of after
        for db in connections:
            call_command('flush', verbosity=0, interactive=False, database=db)
        for conn in connections.all():
            conn.close()
    elif hasattr(item, 'django_unittest'):
        item.django_unittest._post_teardown()
