"""Service-account authentication, scoped per API."""

import os
from functools import lru_cache

from google.oauth2 import service_account

_GA_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
_GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters"]


def _service_account_path() -> str:
    """Resolve the path to the service-account JSON key file."""
    path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_PATH") or os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )
    if not path:
        raise FileNotFoundError(
            "No service-account key found. Set GOOGLE_SERVICE_ACCOUNT_PATH or "
            "GOOGLE_APPLICATION_CREDENTIALS to the path of your JSON key file."
        )
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Service-account key file not found: {path}")
    return path


@lru_cache(maxsize=1)
def get_ga_credentials() -> service_account.Credentials:
    """Return credentials scoped for Google Analytics (read-only)."""
    return service_account.Credentials.from_service_account_file(
        _service_account_path(), scopes=_GA_SCOPES
    )


@lru_cache(maxsize=1)
def get_gsc_credentials() -> service_account.Credentials:
    """Return credentials scoped for Google Search Console."""
    return service_account.Credentials.from_service_account_file(
        _service_account_path(), scopes=_GSC_SCOPES
    )
