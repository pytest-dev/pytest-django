from django.db import connections
from django.core.management import call_command
from django.test.testcases import SimpleTestCase, TransactionTestCase, TestCase


def is_django_unittest(item):
    """
    Returns True if the item is a Django test case, otherwise False.
    """

    return hasattr(item.obj, 'im_class') and issubclass(item.obj.im_class, SimpleTestCase)


def get_django_unittest(item):
    """
    Returns a Django unittest instance that can have _pre_setup() or
    _post_teardown() invoked to setup/teardown the database before a test run.
    """
    if 'transaction_test_case' in item.keywords:
        cls = TransactionTestCase
    else:
        cls = TestCase

    return cls(methodName='__init__')


def django_setup_item(item):
    if 'transaction_test_case' in item.keywords:
        # Nothing needs to be done
        pass
    else:
        # Use the standard TestCase teardown
        get_django_unittest(item)._pre_setup()


def django_teardown_item(item):

    if 'transaction_test_case' in item.keywords:
        # Flush the database and close database connections
        # Django does this by default *before* each test instead of after
        for db in connections:
            call_command('flush', verbosity=0, interactive=False, database=db)

        for conn in connections.all():
            conn.close()
    else:
        # Use the standard TestCase teardown
        get_django_unittest(item)._post_teardown()
