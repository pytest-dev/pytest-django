from .lazy_django import django_is_usable
from .live_server_helper import has_live_server_support


def get_django_base_test_case_class():
    try:
        from django.test import SimpleTestCase
        return SimpleTestCase
    except ImportError:
        from django.test import TestCase
        return TestCase


def is_transaction_test_case(item):

    if 'transaction_test_case' in item.keywords:
        return True

    if has_live_server_support() and 'live_server' in item.funcargs:
        return True

    return False


def is_django_unittest(item):
    """
    Returns True if the item is a Django test case, otherwise False.
    """
    # The test case itself cannot have been created unless Django can be used
    if not django_is_usable():
        return False

    base_class = get_django_base_test_case_class()

    return hasattr(item.obj, 'im_class') and issubclass(item.obj.im_class,
                                                        base_class)


def get_django_unittest(item):
    """
    Returns a Django unittest instance that can have _pre_setup() or
    _post_teardown() invoked to setup/teardown the database before a test run.
    """

    from django.test import TestCase, TransactionTestCase

    if is_transaction_test_case(item):
        cls = TransactionTestCase
    elif item.config.option.no_db:
        cls = TestCase
        cls._fixture_setup = lambda self: None
    else:
        cls = TestCase

    return cls(methodName='__init__')


def django_setup_item(item):
    if not django_is_usable():
        return

    if is_transaction_test_case(item):
        # Nothing needs to be done
        pass
    else:
        # Use the standard TestCase teardown
        get_django_unittest(item)._pre_setup()

    # django_setup_item will not be called if the test is skipped, but teardown
    # will always be called. Set this flag to tell django_teardown_item if
    # it should act or not
    item.keywords['_django_setup'] = True


def django_teardown_item(item):
    if not item.keywords.get('_django_setup'):
        return

    from django.db import connections
    from django.core.management import call_command

    if is_transaction_test_case(item):
        # Flush the database and close database connections
        # Django does this by default *before* each test instead of after
        for db in connections:
            call_command('flush', verbosity=0, interactive=False, database=db)

        for conn in connections.all():
            conn.close()
    else:
        # Use the standard TestCase teardown
        get_django_unittest(item)._post_teardown()
