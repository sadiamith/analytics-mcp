"""Shared fixtures for tests."""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _fake_service_account(tmp_path):
    """Write a minimal fake service-account JSON and point the env var at it."""
    sa = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key123",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIBogIBAAJBALRiMLAHudeSA/x3hB2f+2NRkJLA"
        "hR0rcryEjMGSUyjvFKKl8csb\nkkhIoLR/ZH4kDqxPA2IXEkVz5rMqeWNcZ70CAwEA"
        "AQJAe5z5096oyGOjQBLhFjMN\nkQN5IBiXhTqOmdyPH0HiSFCUkn/XBdG8KXQhoI15"
        "C0UQFFT7NNgYfQs2VvGCKOcZ\nOQIhAOcn6riAzWCfVKzM+0Kwm/A+bN/EBa55KYXZ"
        "sPGH+E5bAiEAyMwrgO7LQlSz\n6Kk/5jQ5bEFnakHLN+sV4MVScN1+E/MCIFqEqAdB"
        "uIGTYR5hUqz9RMy4TLuG/iVZ\nfWdFIY1gy80RAiA6Y9oPUQ+l1GE4dC5S74bNaMCo"
        "hBap6ASq1RKfMqd5JwIhAIul\nolnNGxMBc0TJqfKxaao9cSjIqSUVFWGPODFxlNqE\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    sa_path = tmp_path / "sa.json"
    sa_path.write_text(json.dumps(sa))
    with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_PATH": str(sa_path)}):
        # Clear cached credentials so they pick up the new env var.
        from analytics_mcp.auth import get_ga_credentials, get_gsc_credentials

        get_ga_credentials.cache_clear()
        get_gsc_credentials.cache_clear()
        yield
        get_ga_credentials.cache_clear()
        get_gsc_credentials.cache_clear()


@pytest.fixture()
def mock_gsc_service():
    """Return a MagicMock that acts as a GSC discovery service."""
    return MagicMock()


@pytest.fixture()
def mock_ga_data_client():
    """Return an AsyncMock that acts as a GA Data API async client."""
    return AsyncMock()


@pytest.fixture()
def mock_ga_admin_client():
    """Return an AsyncMock that acts as a GA Admin API async client."""
    return AsyncMock()
