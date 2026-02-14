"""GSC property listing and detail tools."""

from __future__ import annotations

from typing import Any, Dict

from analytics_mcp._clients import _build_gsc_service, run_gsc
from analytics_mcp.errors import handle_api_errors, retry_on_transient
from analytics_mcp.tools._helpers import success, validate_site_url


@handle_api_errors
async def gsc_list_properties() -> Dict[str, Any]:
    """List all Search Console properties accessible to the service account,
    including their permission levels."""

    @retry_on_transient
    def _call() -> Dict[str, Any]:
        service = _build_gsc_service()
        return service.sites().list().execute()

    raw = await run_gsc(_call)
    sites = raw.get("siteEntry", [])
    return success(sites)


@handle_api_errors
async def gsc_get_property_details(site_url: str) -> Dict[str, Any]:
    """Get verification and ownership details for a single GSC property.

    Args:
        site_url: Exact GSC property URL (e.g. 'https://example.com/' or 'sc-domain:example.com').
    """
    validate_site_url(site_url)

    @retry_on_transient
    def _call() -> Dict[str, Any]:
        service = _build_gsc_service()
        return service.sites().get(siteUrl=site_url).execute()

    raw = await run_gsc(_call)
    return success(raw, site_url=site_url)
