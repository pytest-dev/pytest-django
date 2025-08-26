from __future__ import annotations

from typing import Any, cast

import pytest
from _pytest.mark import MarkDecorator

from pytest_django_test.app.models import Item


try:
    import pytest_asyncio
except ImportError:
    pytestmark: MarkDecorator = pytest.mark.skip("pytest-asyncio is not installed")
    fixturemark: MarkDecorator = pytest.mark.skip("pytest-asyncio is not installed")

else:
    pytestmark = pytest.mark.asyncio
    fixturemark = cast(MarkDecorator, pytest_asyncio.fixture)


@pytest.mark.parametrize("run_number", [1, 2])
@pytestmark
@pytest.mark.django_db
async def test_async_db(run_number: int) -> None:  # noqa: ARG001
    # test async database usage remains isolated between tests

    assert await Item.objects.acount() == 0
    # make a new item instance, to be rolled back by the transaction wrapper before the next parametrized run
    await Item.objects.acreate(name="blah")
    assert await Item.objects.acount() == 1


@fixturemark
async def db_item() -> Any:
    return await Item.objects.acreate(name="async")


@pytest.fixture
def sync_db_item() -> Any:
    return Item.objects.create(name="sync")


@pytestmark
@pytest.mark.xfail(strict=True, reason="Sync fixture used in async test")
@pytest.mark.usefixtures("db_item", "sync_db_item")
async def test_db_item() -> None:
    pass


@pytest.mark.xfail(strict=True, reason="Async fixture used in sync test")
def test_sync_db_item(async_db_item: Item, sync_db_item) -> None:
    pass
