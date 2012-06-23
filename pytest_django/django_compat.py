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


def is_transaction_test_case(item):
    mark = getattr(item.obj, 'djangodb', None)
    if mark:
        if mark.transaction:
            return True
        if has_live_server_support() and 'live_server' in item.funcargs:
            # This case is odd, it can only happen if someone marked
            # the function requesting live_server with the djangodb
            # mark, but forgot to add transaction=True.
            return True


def is_django_unittest(item):
    """Returns True if the item is a Django test case, otherwise False"""
    try:
        from django.test import SimpleTestCase as TestCase
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
