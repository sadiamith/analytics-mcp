"""Tests for auth module."""

import os
from unittest.mock import MagicMock, patch

import pytest
from analytics_mcp.auth import _service_account_path, get_ga_credentials, get_gsc_credentials


class TestServiceAccountPath:
    def test_explicit_env_var(self, tmp_path):
        sa = tmp_path / "sa.json"
        sa.write_text("{}")
        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_PATH": str(sa)}, clear=False):
            assert _service_account_path() == str(sa)

    def test_fallback_env_var(self, tmp_path):
        sa = tmp_path / "sa.json"
        sa.write_text("{}")
        env = os.environ.copy()
        env.pop("GOOGLE_SERVICE_ACCOUNT_PATH", None)
        env["GOOGLE_APPLICATION_CREDENTIALS"] = str(sa)
        with patch.dict(os.environ, env, clear=True):
            assert _service_account_path() == str(sa)

    def test_missing_env_var(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(FileNotFoundError, match="No service-account key found"):
                _service_account_path()

    def test_missing_file(self, tmp_path):
        fake = str(tmp_path / "does_not_exist.json")
        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_PATH": fake}, clear=False):
            with pytest.raises(FileNotFoundError, match="not found"):
                _service_account_path()


class TestCredentials:
    def test_ga_credentials_have_readonly_scope(self):
        """GA creds should request analytics.readonly scope."""
        get_ga_credentials.cache_clear()
        mock_creds = MagicMock()
        mock_creds.scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
        with patch(
            "analytics_mcp.auth.service_account.Credentials.from_service_account_file",
            return_value=mock_creds,
        ):
            creds = get_ga_credentials()
            assert "analytics.readonly" in str(creds.scopes)

    def test_gsc_credentials_have_webmasters_scope(self):
        """GSC creds should request webmasters scope."""
        get_gsc_credentials.cache_clear()
        mock_creds = MagicMock()
        mock_creds.scopes = ["https://www.googleapis.com/auth/webmasters"]
        with patch(
            "analytics_mcp.auth.service_account.Credentials.from_service_account_file",
            return_value=mock_creds,
        ):
            creds = get_gsc_credentials()
            assert "webmasters" in str(creds.scopes)

    def test_credentials_are_cached(self):
        get_ga_credentials.cache_clear()
        mock_creds = MagicMock()
        with patch(
            "analytics_mcp.auth.service_account.Credentials.from_service_account_file",
            return_value=mock_creds,
        ):
            c1 = get_ga_credentials()
            c2 = get_ga_credentials()
            assert c1 is c2
