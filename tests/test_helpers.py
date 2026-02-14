"""Tests for _helpers utilities."""

import pytest
from analytics_mcp.tools._helpers import (
    construct_property_rn,
    failure,
    success,
    validate_site_url,
)


class TestResponseEnvelope:
    def test_success_basic(self):
        resp = success({"key": "value"})
        assert resp["ok"] is True
        assert resp["data"] == {"key": "value"}
        assert resp["error"] is None
        assert resp["meta"] is None

    def test_success_with_meta(self):
        resp = success([1, 2], property_id="properties/123")
        assert resp["ok"] is True
        assert resp["meta"]["property_id"] == "properties/123"

    def test_failure_basic(self):
        resp = failure("something broke")
        assert resp["ok"] is False
        assert resp["data"] is None
        assert resp["error"]["message"] == "something broke"
        assert resp["error"]["code"] is None

    def test_failure_with_code(self):
        resp = failure("forbidden", code=403)
        assert resp["error"]["code"] == 403

    def test_envelope_keys(self):
        for resp in [success("x"), failure("x")]:
            assert set(resp.keys()) == {"ok", "data", "error", "meta"}


class TestConstructPropertyRN:
    def test_int(self):
        assert construct_property_rn(12345) == "properties/12345"

    def test_str_number(self):
        assert construct_property_rn("12345") == "properties/12345"

    def test_str_prefixed(self):
        assert construct_property_rn("properties/12345") == "properties/12345"

    def test_str_with_spaces(self):
        assert construct_property_rn("  12345  ") == "properties/12345"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            construct_property_rn("invalid")

    def test_invalid_prefix_raises(self):
        with pytest.raises(ValueError):
            construct_property_rn("properties/abc")


class TestValidateSiteUrl:
    def test_url_prefix(self):
        assert validate_site_url("https://example.com/") == "https://example.com/"

    def test_url_prefix_http(self):
        assert validate_site_url("http://example.com/") == "http://example.com/"

    def test_domain_property(self):
        assert validate_site_url("sc-domain:example.com") == "sc-domain:example.com"

    def test_domain_property_subdomain(self):
        assert validate_site_url("sc-domain:sub.example.com") == "sc-domain:sub.example.com"

    def test_missing_trailing_slash(self):
        with pytest.raises(ValueError):
            validate_site_url("https://example.com")

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            validate_site_url("example.com")
