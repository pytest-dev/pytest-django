"""
Dynamically load all Django assertion cases and expose them for importing
"""
from django.test import (
    TestCase, SimpleTestCase,
    LiveServerTestCase, TransactionTestCase
)


def _wrapper(name):
    def assertion_func(*args, **kwargs):
        getattr(TestCase('run'), name)(*args, **kwargs)

    return assertion_func


__all__ = []
asserts = set()
asserts.update(
    set(attr for attr in TestCase.__dict__ if attr.startswith('assert')),
    set(attr for attr in SimpleTestCase.__dict__ if attr.startswith('assert')),
    set(attr for attr in LiveServerTestCase.__dict__ if attr.startswith('assert')),
    set(attr for attr in TransactionTestCase.__dict__ if attr.startswith('assert')),
)

for assert_func in asserts:
    locals()[assert_func] = _wrapper(assert_func)
    __all__.append(assert_func)
