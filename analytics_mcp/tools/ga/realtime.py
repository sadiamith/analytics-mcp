"""GA realtime report tool."""

from __future__ import annotations

from typing import Any, Dict, List

from google.analytics import data_v1beta

from analytics_mcp._clients import create_data_api_client
from analytics_mcp.errors import handle_api_errors, retry_on_transient
from analytics_mcp.tools._helpers import construct_property_rn, proto_to_dict, success
from analytics_mcp.tools.ga.metadata import (
    get_dimension_filter_hints,
    get_metric_filter_hints,
    get_order_bys_hints,
)


def _run_realtime_report_description() -> str:
    """Build the dynamic description for ``ga_run_realtime_report``."""
    return (
        f"{ga_run_realtime_report.__doc__}\n\n"
        "## Hints for arguments\n\n"
        "### dimensions\n"
        "Use only realtime dimensions from "
        "https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-api-schema#dimensions\n"
        "or user-scoped custom dimensions (apiName starting with 'customUser:').\n\n"
        "### metrics\n"
        "Use only realtime metrics from "
        "https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-api-schema#metrics\n"
        "Custom metrics are not available for realtime reports.\n\n"
        "### dimension_filter\n"
        f"{get_dimension_filter_hints()}\n\n"
        "### metric_filter\n"
        f"{get_metric_filter_hints()}\n\n"
        "### order_bys\n"
        f"{get_order_bys_hints()}\n"
    )


@handle_api_errors
@retry_on_transient
async def ga_run_realtime_report(
    property_id: int | str,
    dimensions: List[str],
    metrics: List[str],
    dimension_filter: Dict[str, Any] | None = None,
    metric_filter: Dict[str, Any] | None = None,
    order_bys: List[Dict[str, Any]] | None = None,
    limit: int | None = None,
    offset: int | None = None,
    return_property_quota: bool = False,
) -> Dict[str, Any]:
    """Run a Google Analytics realtime report.

    See https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-basics

    Args:
        property_id: GA property ID (number or 'properties/12345').
        dimensions: Realtime dimension names.
        metrics: Realtime metric names.
        dimension_filter: FilterExpression dict for dimensions.
        metric_filter: FilterExpression dict for metrics.
        order_bys: List of OrderBy dicts.
        limit: Max rows (≤ 250 000).
        offset: Row offset for pagination.
        return_property_quota: Whether to return quota info.
    """
    request = data_v1beta.RunRealtimeReportRequest(
        property=construct_property_rn(property_id),
        dimensions=[data_v1beta.Dimension(name=d) for d in dimensions],
        metrics=[data_v1beta.Metric(name=m) for m in metrics],
        return_property_quota=return_property_quota,
    )

    if dimension_filter:
        request.dimension_filter = data_v1beta.FilterExpression(dimension_filter)
    if metric_filter:
        request.metric_filter = data_v1beta.FilterExpression(metric_filter)
    if order_bys:
        request.order_bys = [data_v1beta.OrderBy(ob) for ob in order_bys]
    if limit:
        request.limit = limit
    if offset:
        request.offset = offset

    response = await create_data_api_client().run_realtime_report(request)
    return success(proto_to_dict(response), property_id=construct_property_rn(property_id))


# Stored for server.py to register with add_tool using the dynamic description.
run_realtime_report_description = _run_realtime_report_description
