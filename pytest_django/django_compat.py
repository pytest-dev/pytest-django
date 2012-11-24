# Note that all functions here assume django is available.  So ensure
# this is the case before you call them.


def is_django_unittest(item):
    """Returns True if the item is a Django test case, otherwise False"""
    try:
        from django.test import SimpleTestCase as TestCase
    except ImportError:
        from django.test import TestCase

    return (hasattr(item.obj, 'im_class') and
            issubclass(item.obj.im_class, TestCase))
