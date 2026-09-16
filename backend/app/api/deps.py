"""Shared API dependencies (tenant scoping)."""
from __future__ import annotations

import uuid

from fastapi import Header, HTTPException, status


async def get_org_id(
    x_org_id: uuid.UUID = Header(
        ...,
        alias="X-Org-Id",
        description="Tenant/organization id. In production derive this from the "
        "authenticated principal (JWT claim) instead of a header.",
    ),
) -> uuid.UUID:
    """Resolve the active organization for the request.

    This is the single multi-tenancy chokepoint: every CRUD query filters by the
    value returned here. Swap the header for a verified JWT claim to harden.
    """
    if x_org_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-Org-Id"
        )
    return x_org_id
