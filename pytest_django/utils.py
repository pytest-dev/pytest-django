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
    get_django_unittest(item)._pre_setup()


def django_teardown_item(item):
    get_django_unittest(item)._post_teardown()
