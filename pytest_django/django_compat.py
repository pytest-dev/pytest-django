# Note that all functions here assume django is available.  So ensure
# this is the case before you call them.
import sys


def is_django_unittest(item):
    """Returns True if the item is a Django test case, otherwise False"""
    try:
        from django.test import SimpleTestCase as TestCase
    except ImportError:
        from django.test import TestCase

    if sys.version_info < (3, 0):
        return (hasattr(item.obj, 'im_class') and
                issubclass(item.obj.im_class, TestCase))

    return (hasattr(item.obj, '__self__') and
            hasattr(item.obj.__self__, '__class__') and
            issubclass(item.obj.__self__.__class__, TestCase))
