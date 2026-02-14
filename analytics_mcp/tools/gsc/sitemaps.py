"""GSC sitemap management tools — list, details, submit, delete."""

from __future__ import annotations

from typing import Any, Dict

from analytics_mcp._clients import _build_gsc_service, run_gsc
from analytics_mcp.errors import handle_api_errors, retry_on_transient
from analytics_mcp.tools._helpers import success, validate_site_url


# ---------------------------------------------------------------------------
# 1. gsc_list_sitemaps
# ---------------------------------------------------------------------------

@handle_api_errors
async def gsc_list_sitemaps(site_url: str) -> Dict[str, Any]:
    """List all sitemaps for a GSC property with status, dates, and URL counts.

    Args:
        site_url: Exact GSC property URL.
    """
    validate_site_url(site_url)

    @retry_on_transient
    def _call() -> Dict[str, Any]:
        service = _build_gsc_service()
        return service.sitemaps().list(siteUrl=site_url).execute()

    raw = await run_gsc(_call)
    sitemaps = raw.get("sitemap", [])
    return success(sitemaps, site_url=site_url, count=len(sitemaps))


# ---------------------------------------------------------------------------
# 2. gsc_get_sitemap_details
# ---------------------------------------------------------------------------

@handle_api_errors
async def gsc_get_sitemap_details(site_url: str, sitemap_url: str) -> Dict[str, Any]:
    """Get detailed information about a specific sitemap.

    Args:
        site_url: Exact GSC property URL.
        sitemap_url: Full URL of the sitemap to inspect.
    """
    validate_site_url(site_url)

    @retry_on_transient
    def _call() -> Dict[str, Any]:
        service = _build_gsc_service()
        return service.sitemaps().get(siteUrl=site_url, feedpath=sitemap_url).execute()

    raw = await run_gsc(_call)
    return success(raw, site_url=site_url, sitemap_url=sitemap_url)


# ---------------------------------------------------------------------------
# 3. gsc_submit_sitemap
# ---------------------------------------------------------------------------

@handle_api_errors
async def gsc_submit_sitemap(site_url: str, sitemap_url: str) -> Dict[str, Any]:
    """Submit or resubmit a sitemap URL to Google.

    Args:
        site_url: Exact GSC property URL.
        sitemap_url: Full URL of the sitemap to submit.
    """
    validate_site_url(site_url)

    @retry_on_transient
    def _call() -> Dict[str, Any]:
        service = _build_gsc_service()
        service.sitemaps().submit(siteUrl=site_url, feedpath=sitemap_url).execute()
        # Verify by fetching details after submit.
        try:
            details = service.sitemaps().get(siteUrl=site_url, feedpath=sitemap_url).execute()
            return {"submitted": True, "details": details}
        except Exception:
            return {"submitted": True, "details": None}

    raw = await run_gsc(_call)
    return success(raw, site_url=site_url, sitemap_url=sitemap_url)


# ---------------------------------------------------------------------------
# 4. gsc_delete_sitemap
# ---------------------------------------------------------------------------

@handle_api_errors
async def gsc_delete_sitemap(site_url: str, sitemap_url: str) -> Dict[str, Any]:
    """Remove a sitemap from GSC.

    Args:
        site_url: Exact GSC property URL.
        sitemap_url: Full URL of the sitemap to delete.
    """
    validate_site_url(site_url)

    @retry_on_transient
    def _call() -> Dict[str, Any]:
        service = _build_gsc_service()
        service.sitemaps().delete(siteUrl=site_url, feedpath=sitemap_url).execute()
        return {"deleted": True}

    raw = await run_gsc(_call)
    return success(raw, site_url=site_url, sitemap_url=sitemap_url)
