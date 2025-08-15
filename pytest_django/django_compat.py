# Note that all functions here assume django is available.  So ensure
# this is the case before you call them.
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from typing import TypeAlias

    from django.contrib.auth.models import AbstractBaseUser

    _User: TypeAlias = AbstractBaseUser

    _UserModel: TypeAlias = type[_User]

    __all__ = ("_User", "_UserModel")


def is_django_unittest(request_or_item: pytest.FixtureRequest | pytest.Item) -> bool:
    """Returns whether the request or item is a Django test case."""
    from django.test import SimpleTestCase

    cls = getattr(request_or_item, "cls", None)

    if cls is None:
        return False

    return issubclass(cls, SimpleTestCase)
