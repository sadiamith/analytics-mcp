"""GSC URL inspection tools — single and batch."""

from __future__ import annotations

from typing import Any, Dict, List

from analytics_mcp._clients import _build_gsc_service, run_gsc
from analytics_mcp.errors import handle_api_errors, retry_on_transient
from analytics_mcp.tools._helpers import success, validate_site_url


def _extract_inspection(result: Dict[str, Any]) -> Dict[str, Any]:
    """Pull the useful fields out of an inspection result."""
    inspection = result.get("inspectionResult", {})
    index_status = inspection.get("indexStatusResult", {})

    extracted: Dict[str, Any] = {
        "inspection_result_link": inspection.get("inspectionResultLink"),
        "index_status": {
            "verdict": index_status.get("verdict"),
            "coverage_state": index_status.get("coverageState"),
            "last_crawl_time": index_status.get("lastCrawlTime"),
            "page_fetch_state": index_status.get("pageFetchState"),
            "robots_txt_state": index_status.get("robotsTxtState"),
            "indexing_state": index_status.get("indexingState"),
            "google_canonical": index_status.get("googleCanonical"),
            "user_canonical": index_status.get("userCanonical"),
            "crawled_as": index_status.get("crawledAs"),
            "referring_urls": index_status.get("referringUrls"),
        },
    }

    rich = inspection.get("richResultsResult")
    if rich:
        extracted["rich_results"] = {
            "verdict": rich.get("verdict"),
            "detected_items": rich.get("detectedItems", []),
            "issues": rich.get("richResultsIssues", []),
        }

    return extracted


# ---------------------------------------------------------------------------
# 1. gsc_inspect_url
# ---------------------------------------------------------------------------

@handle_api_errors
async def gsc_inspect_url(
    site_url: str,
    page_url: str,
) -> Dict[str, Any]:
    """Full inspection of a single URL — indexing status, crawl info, rich results.

    Args:
        site_url: Exact GSC property URL (e.g. 'https://example.com/' or 'sc-domain:example.com').
        page_url: The specific URL to inspect.
    """
    validate_site_url(site_url)

    @retry_on_transient
    def _call() -> Dict[str, Any]:
        service = _build_gsc_service()
        return service.urlInspection().index().inspect(
            body={"inspectionUrl": page_url, "siteUrl": site_url}
        ).execute()

    raw = await run_gsc(_call)
    return success(_extract_inspection(raw), site_url=site_url, page_url=page_url)


# ---------------------------------------------------------------------------
# 2. gsc_batch_inspect_urls
# ---------------------------------------------------------------------------

@handle_api_errors
async def gsc_batch_inspect_urls(
    site_url: str,
    urls: List[str],
) -> Dict[str, Any]:
    """Inspect up to 10 URLs and return per-URL results plus an issue summary.

    Args:
        site_url: Exact GSC property URL.
        urls: List of page URLs to inspect (max 10).
    """
    validate_site_url(site_url)

    if len(urls) > 10:
        from analytics_mcp.tools._helpers import failure
        return failure("Maximum 10 URLs per batch. Please reduce the list.", code=400)

    @retry_on_transient
    def _call() -> List[Dict[str, Any]]:
        service = _build_gsc_service()
        results = []
        for page_url in urls:
            try:
                resp = service.urlInspection().index().inspect(
                    body={"inspectionUrl": page_url, "siteUrl": site_url}
                ).execute()
                results.append({"url": page_url, "result": _extract_inspection(resp)})
            except Exception as exc:
                results.append({"url": page_url, "error": str(exc)})
        return results

    per_url = await run_gsc(_call)

    # Build categorised issue summary.
    issues: Dict[str, List[str]] = {
        "not_indexed": [],
        "canonical_mismatch": [],
        "robots_blocked": [],
        "fetch_issues": [],
        "errors": [],
    }

    for item in per_url:
        url = item["url"]
        if "error" in item:
            issues["errors"].append(url)
            continue
        idx = item["result"].get("index_status", {})
        verdict = idx.get("verdict", "")
        coverage = (idx.get("coverage_state") or "").lower()
        if verdict != "PASS" or "not indexed" in coverage or "excluded" in coverage:
            issues["not_indexed"].append(url)
        gc = idx.get("google_canonical") or ""
        uc = idx.get("user_canonical") or ""
        if gc and uc and gc != uc:
            issues["canonical_mismatch"].append(url)
        if idx.get("robots_txt_state") == "BLOCKED":
            issues["robots_blocked"].append(url)
        if idx.get("page_fetch_state") not in (None, "SUCCESSFUL"):
            issues["fetch_issues"].append(url)

    return success(
        {"inspections": per_url, "issue_summary": issues},
        site_url=site_url,
        urls_inspected=len(urls),
    )
