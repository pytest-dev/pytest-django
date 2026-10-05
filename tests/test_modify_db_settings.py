"""Regression tests for stale connection wrappers after
``django_db_modify_db_settings`` modifies ``settings.DATABASES``."""

from __future__ import annotations

from .helpers import DjangoPytester


def test_modified_db_settings_used_despite_materialized_connection(
    django_pytester: DjangoPytester,
) -> None:
    """A wrapper materialized before the override must not survive it (#1317).

    The test module touches ``connections["default"]`` (materializing the
    wrapper and the ConnectionHandler's cached settings) *before* the
    session-scoped ``django_db_modify_db_settings`` fixture changes the
    HOST. Without eviction, ``django_db_setup`` keeps serving the stale
    wrapper and connects to the pre-override host — the exact failure mode
    reported with Testcontainers.
    """
    django_pytester.create_test_module(
        """
        import pytest
        from django.conf import settings
        from django.db import connections

        # Materialize the connection wrapper (and the ConnectionHandler's
        # cached settings) from the original settings.DATABASES.
        _ = connections["default"].settings_dict

        ORIGINAL_HOST = connections["default"].settings_dict["HOST"]


        @pytest.fixture(scope="session")
        def django_db_modify_db_settings():
            # Replace the alias entry (as Testcontainers setups do) rather
            # than mutate it in place — this is what strands the cached
            # settings dict that materialized wrappers keep using.
            settings.DATABASES["default"] = {
                **settings.DATABASES["default"],
                "HOST": "modified-host",
            }


        @pytest.mark.django_db
        def test_connection_uses_modified_host(django_db_setup):
            connection = connections["default"]
            assert connection.settings_dict["HOST"] == "modified-host"
    """
    )

    result = django_pytester.runpytest_subprocess("-v")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*test_connection_uses_modified_host PASSED*"])
