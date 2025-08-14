from __future__ import annotations

import threading

import pytest

from pytest_django_test.app.models import Item


@pytest.mark.django_db
def test_sync_db_access_in_non_main_thread_is_blocked() -> None:
    """
    Ensure that when using the sync django_db helper (non-transactional),
    database access from a different thread raises the expected RuntimeError
    stating that DB access is only allowed in the main thread.

    Mirrors the intent of the async equivalent test that checks thread
    safeguards for async contexts.
    """
    captured: list[BaseException | None] = [None]

    def worker() -> None:
        try:
            # Any ORM operation that touches the DB will attempt to ensure a connection.
            # This should raise from the "sync_only" db blocker in non-main threads.
            Item.objects.count()
        except BaseException as exc:  # noqa: BLE001 - we want to capture exactly what is raised
            captured[0] = exc

    t = threading.Thread(target=worker)
    t.start()
    t.join()

    assert captured[0] is not None, "Expected DB access in worker thread to raise an exception"
    assert isinstance(captured[0], RuntimeError)
    assert "only allowed in the main thread" in str(captured[0])
