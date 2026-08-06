from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from django.db import DatabaseError, connections
from django.test import AsyncClient

from pytest_django.fixtures import _override_instance_attribute
from pytest_django_test.app.models import Item, SecondItem


def test_override_instance_attribute_restores_existing_value() -> None:
    instance = SimpleNamespace(value="original")

    def replace_then_raise() -> None:
        with _override_instance_attribute(instance, "value", "replacement"):
            assert instance.value == "replacement"
            raise RuntimeError("test exception")

    with pytest.raises(RuntimeError, match="test exception"):
        replace_then_raise()

    assert instance.value == "original"


@pytest.mark.parametrize("run_number", [1, 2])
@pytest.mark.asyncio
async def test_async_db_rolls_back_between_tests(db: None, run_number: int) -> None:
    del db

    assert await Item.objects.acount() == 0
    await Item.objects.acreate(name=f"async-{run_number}")
    assert await Item.objects.acount() == 1


@pytest.fixture
def sync_db_item(db: None) -> Item:
    del db
    item: Item = Item.objects.create(name="sync fixture")
    return item


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_async_db_shares_connection_with_sync_fixture(sync_db_item: Item) -> None:
    item = await Item.objects.aget(pk=sync_db_item.pk)

    assert item.name == sync_db_item.name


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_async_db_connection_is_shared_with_async_client(
    async_client: AsyncClient,
    sync_db_item: Item,
) -> None:
    response = await async_client.get("/item_count/")

    assert sync_db_item.name == "sync fixture"
    assert response.content == b"Item count: 1"


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_async_db_keeps_other_threads_isolated() -> None:
    main_connection = connections["default"]

    def inspect_other_thread() -> object:
        other_connection = connections["default"]
        with pytest.raises(DatabaseError):
            main_connection.validate_thread_sharing()
        return other_connection

    with ThreadPoolExecutor(max_workers=1) as executor:
        other_connection = executor.submit(inspect_other_thread).result()

    assert other_connection is not main_connection


@pytest.mark.parametrize("run_number", [1, 2])
@pytest.mark.asyncio
async def test_async_transactional_db_flushes_between_tests(
    transactional_db: None,
    run_number: int,
) -> None:
    del transactional_db

    assert await Item.objects.acount() == 0
    await Item.objects.acreate(name=f"transactional-{run_number}")
    assert await Item.objects.acount() == 1


@pytest.mark.asyncio
@pytest.mark.django_db(databases=["default", "second"])
async def test_async_db_shares_all_selected_database_connections() -> None:
    await Item.objects.acreate(name="default")
    await SecondItem.objects.acreate(name="second")

    assert await Item.objects.acount() == 1
    assert await SecondItem.objects.acount() == 1
