from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable
from typing import Any, Callable, ParamSpec, TypeVar, Union

import pytest

from pytest_django_test.app.models import Item


_R = TypeVar("_R", bound=Union[Awaitable[Any], AsyncIterator[Any]])
_P = ParamSpec("_P")
FixtureFunction = Callable[_P, _R]

try:
    import pytest_asyncio
except ImportError:
    pytestmark: Callable[[FixtureFunction[_P, _R]], FixtureFunction[_P, _R]] = pytest.mark.skip(
        "pytest-asyncio is not installed"
    )
    fixturemark: Callable[[FixtureFunction[_P, _R]], FixtureFunction[_P, _R]] = pytest.mark.skip(
        "pytest-asyncio is not installed"
    )

else:
    pytestmark = pytest.mark.asyncio
    fixturemark = pytest_asyncio.fixture


@pytest.mark.parametrize("run_number", [1, 2])
@pytestmark
@pytest.mark.django_db
async def test_async_db(db, run_number) -> None:
    # test async database usage remains isolated between tests

    assert await Item.objects.acount() == 0
    # make a new item instance, to be rolled back by the transaction wrapper before the next parametrized run
    await Item.objects.acreate(name="blah")
    assert await Item.objects.acount() == 1


@fixturemark
async def db_item(db) -> Any:
    return await Item.objects.acreate(name="async")


@pytest.fixture
def sync_db_item(db) -> Any:
    return Item.objects.create(name="sync")


@pytestmark
@pytest.mark.xfail(strict=True, reason="Sync fixture used in async test")
async def test_db_item(db_item: Item, sync_db_item) -> None:
    pass


@pytest.mark.xfail(strict=True, reason="Async fixture used in sync test")
def test_sync_db_item(async_db_item: Item, sync_db_item) -> None:
    pass
