"""GA custom dimensions/metrics and hint generators for report tools."""

from __future__ import annotations

from typing import Any, Dict

from google.analytics import data_v1beta

from analytics_mcp._clients import create_data_api_client
from analytics_mcp.errors import handle_api_errors, retry_on_transient
from analytics_mcp.tools._helpers import construct_property_rn, proto_to_dict, proto_to_json, success


# ---------------------------------------------------------------------------
# Hint generators (used by reports.py and realtime.py descriptions)
# ---------------------------------------------------------------------------

def get_date_ranges_hints() -> str:
    r1 = data_v1beta.DateRange(start_date="2025-01-01", end_date="2025-01-31", name="Jan2025")
    r2 = data_v1beta.DateRange(start_date="2025-02-01", end_date="2025-02-28", name="Feb2025")
    r3 = data_v1beta.DateRange(start_date="yesterday", end_date="today", name="YesterdayAndToday")
    r4 = data_v1beta.DateRange(start_date="30daysAgo", end_date="yesterday", name="Previous30Days")

    return (
        "Example date_range arguments:\n"
        f"  1. Single date range:  [ {proto_to_json(r1)} ]\n"
        f"  2. Relative (yesterday/today):  [ {proto_to_json(r3)} ]\n"
        f"  3. Relative (NdaysAgo):  [ {proto_to_json(r4)} ]\n"
        f"  4. Multiple ranges:  [ {proto_to_json(r1)}, {proto_to_json(r2)} ]"
    )


_FILTER_NOTES = (
    "\n  Notes:\n"
    "    dimension_filter and metric_filter are applied independently.\n"
    "    Complex cross-filter conditions (e.g. eventName='page_view' AND eventCount>100 OR\n"
    "    eventName='join_group' AND eventCount<50) cannot be expressed in a single request.\n"
    "    Either run a broader report and filter client-side, or run separate reports.\n"
)


def get_dimension_filter_hints() -> str:
    begins_with = data_v1beta.FilterExpression(
        filter=data_v1beta.Filter(
            field_name="eventName",
            string_filter=data_v1beta.Filter.StringFilter(
                match_type=data_v1beta.Filter.StringFilter.MatchType.BEGINS_WITH, value="add"
            ),
        )
    )
    not_filter = data_v1beta.FilterExpression(not_expression=begins_with)
    in_list = data_v1beta.FilterExpression(
        filter=data_v1beta.Filter(
            field_name="eventName",
            in_list_filter=data_v1beta.Filter.InListFilter(
                case_sensitive=True, values=["first_visit", "purchase", "add_to_cart"]
            ),
        )
    )
    return (
        "Example dimension_filter arguments:\n"
        f"  1. Begins-with: {proto_to_json(begins_with)}\n"
        f"  2. NOT filter:  {proto_to_json(not_filter)}\n"
        f"  3. In-list:     {proto_to_json(in_list)}"
        + _FILTER_NOTES
    )


def get_metric_filter_hints() -> str:
    gt_10 = data_v1beta.FilterExpression(
        filter=data_v1beta.Filter(
            field_name="eventCount",
            numeric_filter=data_v1beta.Filter.NumericFilter(
                operation=data_v1beta.Filter.NumericFilter.Operation.GREATER_THAN,
                value=data_v1beta.NumericValue(int64_value=10),
            ),
        )
    )
    between = data_v1beta.FilterExpression(
        filter=data_v1beta.Filter(
            field_name="purchaseRevenue",
            between_filter=data_v1beta.Filter.BetweenFilter(
                from_value=data_v1beta.NumericValue(double_value=10.0),
                to_value=data_v1beta.NumericValue(double_value=25.0),
            ),
        )
    )
    return (
        "Example metric_filter arguments:\n"
        f"  1. Greater-than:  {proto_to_json(gt_10)}\n"
        f"  2. Between:       {proto_to_json(between)}"
        + _FILTER_NOTES
    )


def get_order_bys_hints() -> str:
    dim_asc = data_v1beta.OrderBy(
        dimension=data_v1beta.OrderBy.DimensionOrderBy(
            dimension_name="eventName",
            order_type=data_v1beta.OrderBy.DimensionOrderBy.OrderType.ALPHANUMERIC,
        ),
        desc=False,
    )
    metric_desc = data_v1beta.OrderBy(
        metric=data_v1beta.OrderBy.MetricOrderBy(metric_name="eventValue"), desc=True
    )
    return (
        "Example order_bys arguments:\n"
        f"  1. Dimension ascending:  [ {proto_to_json(dim_asc)} ]\n"
        f"  2. Metric descending:    [ {proto_to_json(metric_desc)} ]\n"
        f"  3. Combined:             [ {proto_to_json(dim_asc)}, {proto_to_json(metric_desc)} ]\n"
        "\n  Dimensions/metrics in order_bys must also be in the request's dimensions/metrics lists."
    )


# ---------------------------------------------------------------------------
# Tool: ga_get_custom_dimensions_and_metrics
# ---------------------------------------------------------------------------

@handle_api_errors
@retry_on_transient
async def ga_get_custom_dimensions_and_metrics(
    property_id: int | str,
) -> Dict[str, Any]:
    """Returns custom dimensions and metrics defined for a GA property.

    Args:
        property_id: GA property ID (number or 'properties/12345').
    """
    metadata = await create_data_api_client().get_metadata(
        name=f"{construct_property_rn(property_id)}/metadata"
    )
    custom_metrics = [proto_to_dict(m) for m in metadata.metrics if m.custom_definition]
    custom_dimensions = [proto_to_dict(d) for d in metadata.dimensions if d.custom_definition]
    return success(
        {"custom_dimensions": custom_dimensions, "custom_metrics": custom_metrics},
        property_id=construct_property_rn(property_id),
    )
