"""Shared utilities: response envelope helpers, proto conversion, validation."""

from __future__ import annotations

import re
from typing import Any, Dict

import proto


# ---------------------------------------------------------------------------
# Response envelope
# ---------------------------------------------------------------------------

def success(data: Any, **meta: Any) -> Dict[str, Any]:
    """Build a successful response envelope."""
    return {"ok": True, "data": data, "error": None, "meta": meta or None}


def failure(message: str, code: int | None = None, details: Any = None) -> Dict[str, Any]:
    """Build an error response envelope."""
    return {
        "ok": False,
        "data": None,
        "error": {"message": message, "code": code, "details": details},
        "meta": None,
    }


# ---------------------------------------------------------------------------
# Proto helpers (GA)
# ---------------------------------------------------------------------------

def proto_to_dict(obj: proto.Message) -> Dict[str, Any]:
    """Convert a protobuf message to a plain dict."""
    return type(obj).to_dict(obj, use_integers_for_enums=False, preserving_proto_field_name=True)


def proto_to_json(obj: proto.Message) -> str:
    """Convert a protobuf message to a JSON string."""
    return type(obj).to_json(obj, indent=None, preserving_proto_field_name=True)


# ---------------------------------------------------------------------------
# GA property ID normalisation
# ---------------------------------------------------------------------------

def construct_property_rn(property_value: int | str) -> str:
    """Return a GA property resource name like ``properties/12345``."""
    property_num: int | None = None

    if isinstance(property_value, int):
        property_num = property_value
    elif isinstance(property_value, str):
        property_value = property_value.strip()
        if property_value.isdigit():
            property_num = int(property_value)
        elif property_value.startswith("properties/"):
            numeric_part = property_value.split("/")[-1]
            if numeric_part.isdigit():
                property_num = int(numeric_part)

    if property_num is None:
        raise ValueError(
            f"Invalid property ID: {property_value}. "
            "A valid property value is either a number or a string starting "
            "with 'properties/' followed by a number."
        )
    return f"properties/{property_num}"


# ---------------------------------------------------------------------------
# GSC site URL validation
# ---------------------------------------------------------------------------

_DOMAIN_PROPERTY_RE = re.compile(r"^sc-domain:[a-zA-Z0-9][-a-zA-Z0-9.]+\.[a-zA-Z]{2,}$")
_URL_PREFIX_RE = re.compile(r"^https?://.+/$")


def validate_site_url(url: str) -> str:
    """Validate that *url* looks like a valid GSC property identifier.

    Returns the url unchanged if valid, raises ValueError otherwise.
    GSC requires exact format — we validate but never modify.
    """
    if _DOMAIN_PROPERTY_RE.match(url) or _URL_PREFIX_RE.match(url):
        return url
    raise ValueError(
        f"Invalid GSC site URL: {url!r}. "
        "Use a URL-prefix property (e.g. 'https://example.com/') "
        "or a domain property (e.g. 'sc-domain:example.com')."
    )
