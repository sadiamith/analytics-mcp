"""Entry point for the combined Analytics MCP server."""

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Singleton MCP instance
# ---------------------------------------------------------------------------
mcp = FastMCP("Analytics MCP Server")

# ---------------------------------------------------------------------------
# GA tools — decorator-based registration
# ---------------------------------------------------------------------------
from analytics_mcp.tools.ga.accounts import (  # noqa: E402
    ga_get_account_summaries,
    ga_get_property_details,
    ga_list_google_ads_links,
    ga_list_property_annotations,
)
from analytics_mcp.tools.ga.metadata import (  # noqa: E402
    ga_get_custom_dimensions_and_metrics,
)
from analytics_mcp.tools.ga.reports import (  # noqa: E402
    ga_run_report,
    run_report_description,
)
from analytics_mcp.tools.ga.realtime import (  # noqa: E402
    ga_run_realtime_report,
    run_realtime_report_description,
)

# Register GA tools with simple descriptions.
mcp.tool()(ga_get_account_summaries)
mcp.tool()(ga_get_property_details)
mcp.tool()(ga_list_google_ads_links)
mcp.tool()(ga_list_property_annotations)
mcp.tool()(ga_get_custom_dimensions_and_metrics)

# Reports/realtime use dynamic descriptions generated at import time.
mcp.add_tool(
    ga_run_report,
    title="Run a Google Analytics report",
    description=run_report_description(),
)
mcp.add_tool(
    ga_run_realtime_report,
    title="Run a Google Analytics realtime report",
    description=run_realtime_report_description(),
)

# ---------------------------------------------------------------------------
# GSC tools
# ---------------------------------------------------------------------------
from analytics_mcp.tools.gsc.properties import (  # noqa: E402
    gsc_list_properties,
    gsc_get_property_details,
)
from analytics_mcp.tools.gsc.search_analytics import (  # noqa: E402
    gsc_search_analytics,
    gsc_compare_search_periods,
    gsc_search_overview,
)
from analytics_mcp.tools.gsc.url_inspection import (  # noqa: E402
    gsc_inspect_url,
    gsc_batch_inspect_urls,
)
from analytics_mcp.tools.gsc.sitemaps import (  # noqa: E402
    gsc_list_sitemaps,
    gsc_get_sitemap_details,
    gsc_submit_sitemap,
    gsc_delete_sitemap,
)

mcp.tool()(gsc_list_properties)
mcp.tool()(gsc_get_property_details)
mcp.tool()(gsc_search_analytics)
mcp.tool()(gsc_compare_search_periods)
mcp.tool()(gsc_search_overview)
mcp.tool()(gsc_inspect_url)
mcp.tool()(gsc_batch_inspect_urls)
mcp.tool()(gsc_list_sitemaps)
mcp.tool()(gsc_get_sitemap_details)
mcp.tool()(gsc_submit_sitemap)
mcp.tool()(gsc_delete_sitemap)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_server() -> None:
    """Start the MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    run_server()
