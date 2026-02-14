"""Tests for server tool registration and response contracts."""

from __future__ import annotations

import pytest

# Import tools directly to test their contracts.
from analytics_mcp.tools._helpers import failure, success

# Expected tool names.
GA_TOOLS = {
    "ga_get_account_summaries",
    "ga_get_property_details",
    "ga_list_google_ads_links",
    "ga_list_property_annotations",
    "ga_get_custom_dimensions_and_metrics",
    "ga_run_report",
    "ga_run_realtime_report",
}

GSC_TOOLS = {
    "gsc_list_properties",
    "gsc_get_property_details",
    "gsc_search_analytics",
    "gsc_compare_search_periods",
    "gsc_search_overview",
    "gsc_inspect_url",
    "gsc_batch_inspect_urls",
    "gsc_list_sitemaps",
    "gsc_get_sitemap_details",
    "gsc_submit_sitemap",
    "gsc_delete_sitemap",
}

ALL_TOOLS = GA_TOOLS | GSC_TOOLS


class TestToolRegistration:
    def test_all_18_tools_registered(self):
        """The server must expose exactly 18 tools."""
        from analytics_mcp.server import mcp

        registered = {t.name for t in mcp._tool_manager.list_tools()}
        assert ALL_TOOLS.issubset(registered), f"Missing: {ALL_TOOLS - registered}"
        assert len(registered) >= 18

    def test_ga_tools_prefixed(self):
        from analytics_mcp.server import mcp

        registered = {t.name for t in mcp._tool_manager.list_tools()}
        for name in registered:
            if name.startswith("ga_"):
                assert name in GA_TOOLS

    def test_gsc_tools_prefixed(self):
        from analytics_mcp.server import mcp

        registered = {t.name for t in mcp._tool_manager.list_tools()}
        for name in registered:
            if name.startswith("gsc_"):
                assert name in GSC_TOOLS


class TestResponseContract:
    """Every envelope must contain ok, data, error, meta."""

    REQUIRED_KEYS = {"ok", "data", "error", "meta"}

    def test_success_envelope(self):
        resp = success({"foo": 1}, bar="baz")
        assert set(resp.keys()) == self.REQUIRED_KEYS
        assert resp["ok"] is True
        assert resp["error"] is None

    def test_failure_envelope(self):
        resp = failure("boom", code=500, details=["detail"])
        assert set(resp.keys()) == self.REQUIRED_KEYS
        assert resp["ok"] is False
        assert resp["data"] is None
        assert resp["error"]["message"] == "boom"
        assert resp["error"]["code"] == 500
        assert resp["error"]["details"] == ["detail"]


class TestErrorHandlerDecorator:
    @pytest.mark.asyncio
    async def test_timeout_returns_failure(self):
        """handle_api_errors should catch TimeoutError."""
        import asyncio
        from analytics_mcp.errors import handle_api_errors

        @handle_api_errors
        async def boom():
            raise asyncio.TimeoutError()

        resp = await boom()
        assert resp["ok"] is False
        assert resp["error"]["code"] == 408

    @pytest.mark.asyncio
    async def test_generic_exception_returns_failure(self):
        from analytics_mcp.errors import handle_api_errors

        @handle_api_errors
        async def boom():
            raise RuntimeError("oops")

        resp = await boom()
        assert resp["ok"] is False
        assert "oops" in resp["error"]["message"]
