"""GSC search analytics tools — query, compare, overview."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from analytics_mcp._clients import _build_gsc_service, run_gsc
from analytics_mcp.errors import handle_api_errors, retry_on_transient
from analytics_mcp.tools._helpers import success, validate_site_url


# ---------------------------------------------------------------------------
# 1. gsc_search_analytics  (replaces get_search_analytics,
#    get_advanced_search_analytics, get_search_by_page_query)
# ---------------------------------------------------------------------------

@handle_api_errors
async def gsc_search_analytics(
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: List[str] | None = None,
    search_type: str = "web",
    row_limit: int = 1000,
    start_row: int = 0,
    dimension_filters: List[Dict[str, str]] | None = None,
    sort_by: str | None = None,
    sort_direction: str = "descending",
) -> Dict[str, Any]:
    """Query GSC search analytics data with dimensions, filters, sorting, and pagination.

    Args:
        site_url: Exact GSC property URL.
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        dimensions: Dimensions to group by (query, page, device, country, date, searchAppearance).
        search_type: Type of results — web, image, video, news, discover.
        row_limit: Max rows to return (≤ 25 000).
        start_row: Row offset for pagination.
        dimension_filters: List of filter dicts, each with keys: dimension, operator, expression.
            operator is one of: contains, equals, notContains, notEquals, includingRegex, excludingRegex.
        sort_by: Metric to sort by (clicks, impressions, ctr, position).
        sort_direction: ascending or descending.
    """
    validate_site_url(site_url)

    body: Dict[str, Any] = {
        "startDate": start_date,
        "endDate": end_date,
        "rowLimit": min(row_limit, 25000),
        "startRow": start_row,
        "searchType": search_type.upper(),
    }

    if dimensions:
        body["dimensions"] = dimensions

    if dimension_filters:
        body["dimensionFilterGroups"] = [{"filters": dimension_filters}]

    if sort_by:
        metric_map = {
            "clicks": "CLICK_COUNT",
            "impressions": "IMPRESSION_COUNT",
            "ctr": "CTR",
            "position": "POSITION",
        }
        if sort_by in metric_map:
            body["orderBy"] = [
                {"metric": metric_map[sort_by], "direction": sort_direction.lower()}
            ]

    @retry_on_transient
    def _call() -> Dict[str, Any]:
        service = _build_gsc_service()
        return service.searchanalytics().query(siteUrl=site_url, body=body).execute()

    raw = await run_gsc(_call)
    rows = raw.get("rows", [])
    return success(
        rows,
        site_url=site_url,
        date_range={"start": start_date, "end": end_date},
        row_count=len(rows),
    )


# ---------------------------------------------------------------------------
# 2. gsc_compare_search_periods
# ---------------------------------------------------------------------------

@handle_api_errors
async def gsc_compare_search_periods(
    site_url: str,
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    dimensions: List[str] | None = None,
    row_limit: int = 1000,
) -> Dict[str, Any]:
    """Compare search analytics between two date ranges with computed deltas.

    Args:
        site_url: Exact GSC property URL.
        period1_start: Start date for period 1 (YYYY-MM-DD).
        period1_end: End date for period 1 (YYYY-MM-DD).
        period2_start: Start date for period 2 (YYYY-MM-DD).
        period2_end: End date for period 2 (YYYY-MM-DD).
        dimensions: Dimensions to group by (default: ['query']).
        row_limit: Max rows per period (≤ 25 000).
    """
    validate_site_url(site_url)
    dims = dimensions or ["query"]

    def _make_body(start: str, end: str) -> Dict[str, Any]:
        return {
            "startDate": start,
            "endDate": end,
            "dimensions": dims,
            "rowLimit": min(row_limit, 25000),
        }

    @retry_on_transient
    def _call() -> Dict[str, Any]:
        service = _build_gsc_service()
        p1 = service.searchanalytics().query(
            siteUrl=site_url, body=_make_body(period1_start, period1_end)
        ).execute()
        p2 = service.searchanalytics().query(
            siteUrl=site_url, body=_make_body(period2_start, period2_end)
        ).execute()
        return {"period1": p1, "period2": p2}

    raw = await run_gsc(_call)

    p1_rows = {tuple(r.get("keys", [])): r for r in raw["period1"].get("rows", [])}
    p2_rows = {tuple(r.get("keys", [])): r for r in raw["period2"].get("rows", [])}
    all_keys = set(p1_rows) | set(p2_rows)

    comparisons = []
    for key in all_keys:
        r1 = p1_rows.get(key, {})
        r2 = p2_rows.get(key, {})

        p1c = r1.get("clicks", 0)
        p2c = r2.get("clicks", 0)
        p1i = r1.get("impressions", 0)
        p2i = r2.get("impressions", 0)

        comparisons.append({
            "keys": list(key),
            "period1": {"clicks": p1c, "impressions": p1i, "ctr": r1.get("ctr", 0), "position": r1.get("position", 0)},
            "period2": {"clicks": p2c, "impressions": p2i, "ctr": r2.get("ctr", 0), "position": r2.get("position", 0)},
            "delta": {
                "clicks": p2c - p1c,
                "clicks_pct": ((p2c - p1c) / p1c * 100) if p1c > 0 else None,
                "impressions": p2i - p1i,
                "impressions_pct": ((p2i - p1i) / p1i * 100) if p1i > 0 else None,
                "ctr": r2.get("ctr", 0) - r1.get("ctr", 0),
                "position": r1.get("position", 0) - r2.get("position", 0),
            },
        })

    comparisons.sort(key=lambda x: abs(x["delta"]["clicks"]), reverse=True)

    return success(
        comparisons,
        site_url=site_url,
        period1={"start": period1_start, "end": period1_end},
        period2={"start": period2_start, "end": period2_end},
        dimensions=dims,
    )


# ---------------------------------------------------------------------------
# 3. gsc_search_overview
# ---------------------------------------------------------------------------

@handle_api_errors
async def gsc_search_overview(
    site_url: str,
    days: int = 28,
) -> Dict[str, Any]:
    """High-level performance overview: totals + daily trend.

    Args:
        site_url: Exact GSC property URL.
        days: Number of days to look back (default 28).
    """
    validate_site_url(site_url)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    @retry_on_transient
    def _call() -> Dict[str, Any]:
        service = _build_gsc_service()
        totals = service.searchanalytics().query(
            siteUrl=site_url,
            body={"startDate": start_str, "endDate": end_str, "dimensions": [], "rowLimit": 1},
        ).execute()
        daily = service.searchanalytics().query(
            siteUrl=site_url,
            body={"startDate": start_str, "endDate": end_str, "dimensions": ["date"], "rowLimit": days},
        ).execute()
        return {"totals": totals, "daily": daily}

    raw = await run_gsc(_call)

    total_row = (raw["totals"].get("rows") or [{}])[0]
    daily_rows = sorted(raw["daily"].get("rows", []), key=lambda r: r.get("keys", [""])[0])

    overview = {
        "totals": {
            "clicks": total_row.get("clicks", 0),
            "impressions": total_row.get("impressions", 0),
            "ctr": total_row.get("ctr", 0),
            "position": total_row.get("position", 0),
        },
        "daily": [
            {
                "date": r["keys"][0],
                "clicks": r.get("clicks", 0),
                "impressions": r.get("impressions", 0),
                "ctr": r.get("ctr", 0),
                "position": r.get("position", 0),
            }
            for r in daily_rows
        ],
    }

    return success(
        overview,
        site_url=site_url,
        date_range={"start": start_str, "end": end_str},
    )
