# Note that all functions here assume django is available.  So ensure
# this is the case before you call them.

import pkg_resources


IS_DJANGO_2 = pkg_resources.get_distribution("Django").version < '3'


def is_django_unittest(request_or_item) -> bool:
    """Returns True if the request_or_item is a Django test case, otherwise False"""
    from django.test import SimpleTestCase

    cls = getattr(request_or_item, "cls", None)

    if cls is None:
        return False

    return issubclass(cls, SimpleTestCase)
