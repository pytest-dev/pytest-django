# Note that all functions here assume django is available.  So ensure
# this is the case before you call them.


def is_django_unittest(request_or_item):
    """Returns True if the request_or_item is a Django test case, otherwise False"""
    try:
        from django.test import SimpleTestCase as TestCase
    except ImportError:
        from django.test import TestCase

    cls = getattr(request_or_item, 'cls', None)

    if cls is None:
        return False

    return issubclass(cls, TestCase)
