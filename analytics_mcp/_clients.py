"""Lazy-init API client factories for GA and GSC."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypeVar

from google.analytics import admin_v1alpha, admin_v1beta, data_v1beta
from google.api_core.gapic_v1.client_info import ClientInfo
from googleapiclient.discovery import build

from analytics_mcp.auth import get_ga_credentials, get_gsc_credentials

T = TypeVar("T")

# Custom user-agent for all GA requests.
_CLIENT_INFO = ClientInfo(user_agent="analytics-mcp/0.1.0")

# Bounded thread pool for sync GSC calls.
_gsc_executor = ThreadPoolExecutor(max_workers=4)

_GSC_TIMEOUT = 30  # seconds


# ---------------------------------------------------------------------------
# GA async clients (protobuf-based)
# ---------------------------------------------------------------------------

def create_admin_api_client() -> admin_v1beta.AnalyticsAdminServiceAsyncClient:
    """Return a GA Admin API (v1beta) async client."""
    return admin_v1beta.AnalyticsAdminServiceAsyncClient(
        client_info=_CLIENT_INFO, credentials=get_ga_credentials()
    )


def create_data_api_client() -> data_v1beta.BetaAnalyticsDataAsyncClient:
    """Return a GA Data API (v1beta) async client."""
    return data_v1beta.BetaAnalyticsDataAsyncClient(
        client_info=_CLIENT_INFO, credentials=get_ga_credentials()
    )


def create_admin_alpha_api_client() -> admin_v1alpha.AnalyticsAdminServiceAsyncClient:
    """Return a GA Admin API (v1alpha) async client."""
    return admin_v1alpha.AnalyticsAdminServiceAsyncClient(
        client_info=_CLIENT_INFO, credentials=get_ga_credentials()
    )


# ---------------------------------------------------------------------------
# GSC sync client (REST, google-api-python-client)
# ---------------------------------------------------------------------------

def _build_gsc_service() -> Any:
    """Create a *fresh* GSC service instance (thread-safe: one per call)."""
    creds = get_gsc_credentials()
    return build("searchconsole", "v1", credentials=creds)


async def run_gsc(fn: Callable[..., T]) -> T:
    """Run a synchronous GSC callable in the bounded thread pool with timeout.

    *fn* should be a zero-arg callable that creates its own service via
    ``_build_gsc_service()`` internally to avoid sharing objects across threads.
    """
    loop = asyncio.get_running_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(_gsc_executor, fn),
        timeout=_GSC_TIMEOUT,
    )
