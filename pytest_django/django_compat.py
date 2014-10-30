# Note that all functions here assume django is available.  So ensure
# this is the case before you call them.
import sys


def is_django_unittest(item):
    """Returns True if the item is a Django test case, otherwise False"""
    try:
        from django.test import SimpleTestCase as TestCase
    except ImportError:
        from django.test import TestCase

    if not hasattr(item, 'cls') or item.cls is None:
        return False

    return issubclass(item.cls, TestCase)
