"""GA account and property admin tools."""

from __future__ import annotations

from typing import Any, Dict, List

from google.analytics import admin_v1alpha, admin_v1beta

from analytics_mcp._clients import (
    create_admin_alpha_api_client,
    create_admin_api_client,
)
from analytics_mcp.errors import handle_api_errors, retry_on_transient
from analytics_mcp.tools._helpers import construct_property_rn, proto_to_dict, success


@handle_api_errors
@retry_on_transient
async def ga_get_account_summaries() -> Dict[str, Any]:
    """List all GA accounts and their properties accessible to the service account."""
    pager = await create_admin_api_client().list_account_summaries()
    pages: List[Dict[str, Any]] = [proto_to_dict(page) async for page in pager]
    return success(pages)


@handle_api_errors
@retry_on_transient
async def ga_get_property_details(property_id: int | str) -> Dict[str, Any]:
    """Get detailed information about a specific GA property.

    Args:
        property_id: GA property ID (number or 'properties/12345').
    """
    client = create_admin_api_client()
    request = admin_v1beta.GetPropertyRequest(name=construct_property_rn(property_id))
    response = await client.get_property(request=request)
    return success(proto_to_dict(response), property_id=construct_property_rn(property_id))


@handle_api_errors
@retry_on_transient
async def ga_list_google_ads_links(property_id: int | str) -> Dict[str, Any]:
    """List Google Ads links for a GA property.

    Args:
        property_id: GA property ID (number or 'properties/12345').
    """
    request = admin_v1beta.ListGoogleAdsLinksRequest(
        parent=construct_property_rn(property_id)
    )
    pager = await create_admin_api_client().list_google_ads_links(request=request)
    pages: List[Dict[str, Any]] = [proto_to_dict(page) async for page in pager]
    return success(pages, property_id=construct_property_rn(property_id))


@handle_api_errors
@retry_on_transient
async def ga_list_property_annotations(property_id: int | str) -> Dict[str, Any]:
    """List date annotations on a GA property.

    Annotations record service releases, marketing campaigns, or traffic changes.

    Args:
        property_id: GA property ID (number or 'properties/12345').
    """
    request = admin_v1alpha.ListReportingDataAnnotationsRequest(
        parent=construct_property_rn(property_id)
    )
    pager = await create_admin_alpha_api_client().list_reporting_data_annotations(
        request=request
    )
    pages: List[Dict[str, Any]] = [proto_to_dict(page) async for page in pager]
    return success(pages, property_id=construct_property_rn(property_id))
