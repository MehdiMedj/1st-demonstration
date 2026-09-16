"""Pytest fixtures. Assumes migrations have been applied (CI runs
`alembic upgrade head` first) against the configured database.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import engine
from app.main import app

# The demo tenant created by the initial migration.
DEMO_ORG_ID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Org-Id": DEMO_ORG_ID},
    ) as c:
        yield c
    # Dispose the pool within this test's event loop so asyncpg connections are
    # never reused across the per-test loops pytest-asyncio creates.
    await engine.dispose()
