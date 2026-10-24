"""Shared test-run safety guards."""

from __future__ import annotations

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Prevent xdist workers from racing the shared schema-reset DB fixture."""

    database_url = os.environ.get("CROWLEY_TEST_DATABASE_URL")
    workers = getattr(config.option, "numprocesses", None)
    if not database_url or workers in (None, 0, "0"):
        return
    raise pytest.UsageError(
        "CROWLEY_TEST_DATABASE_URL uses schema-reset fixtures and cannot run with xdist; "
        "rerun the database tests with -n0 (see docs/TESTING.md)"
    )
