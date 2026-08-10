"""
Dynamically load all Django assertion cases and expose them for importing.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib.messages.test import MessagesTestMixin
from django.test import LiveServerTestCase, SimpleTestCase, TestCase, TransactionTestCase


class MessagesTestCase(MessagesTestMixin, TestCase):
    pass


test_case = MessagesTestCase("run")


def _wrapper(name: str) -> Callable[..., Any]:
    func = getattr(test_case, name)

    @wraps(func)
    def assertion_func(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return assertion_func


__all__ = []
assertions_names: set[str] = set()
assertions_names.update(
    {attr for attr in vars(TestCase) if attr.startswith("assert")},
    {attr for attr in vars(SimpleTestCase) if attr.startswith("assert")},
    {attr for attr in vars(LiveServerTestCase) if attr.startswith("assert")},
    {attr for attr in vars(TransactionTestCase) if attr.startswith("assert")},
    {attr for attr in vars(MessagesTestMixin) if attr.startswith("assert")},
)

for assert_func in assertions_names:
    globals()[assert_func] = _wrapper(assert_func)
    __all__.append(assert_func)  # noqa: PYI056
