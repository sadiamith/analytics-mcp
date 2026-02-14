"""Custom exceptions and error-handling decorators."""

import asyncio
import functools
import logging
import random
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

# Transient HTTP status codes that warrant a retry.
_RETRYABLE_CODES = {429, 500, 502, 503}
_MAX_RETRIES = 3
_BASE_DELAY = 1.0  # seconds


def _is_retryable(exc: Exception) -> bool:
    """Return True if *exc* represents a transient API failure."""
    # google-api-python-client HttpError
    try:
        from googleapiclient.errors import HttpError

        if isinstance(exc, HttpError):
            return exc.resp.status in _RETRYABLE_CODES
    except ImportError:
        pass

    # google-cloud protobuf-based errors
    try:
        from google.api_core.exceptions import GoogleAPICallError

        if isinstance(exc, GoogleAPICallError):
            return exc.code in _RETRYABLE_CODES
    except ImportError:
        pass

    return False


def retry_on_transient(fn: Callable) -> Callable:
    """Decorator – retries a function on transient API errors.

    Uses exponential back-off: 1 s, 2 s, 4 s (jittered), up to 3 attempts.
    Works for both sync and async callables.
    """

    @functools.wraps(fn)
    async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                return await fn(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                if not _is_retryable(exc) or attempt == _MAX_RETRIES - 1:
                    raise
                delay = _BASE_DELAY * (2**attempt) + random.uniform(0, 0.5)
                logger.warning(
                    "Retryable error (attempt %d/%d): %s – retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
        raise last_exc  # type: ignore[misc]

    @functools.wraps(fn)
    def _sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        import time

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                if not _is_retryable(exc) or attempt == _MAX_RETRIES - 1:
                    raise
                delay = _BASE_DELAY * (2**attempt) + random.uniform(0, 0.5)
                logger.warning(
                    "Retryable error (attempt %d/%d): %s – retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    exc,
                    delay,
                )
                time.sleep(delay)
        raise last_exc  # type: ignore[misc]

    return _async_wrapper if asyncio.iscoroutinefunction(fn) else _sync_wrapper


def _parse_gsc_http_error(exc: Any) -> Dict[str, Any]:
    """Extract structured info from a googleapiclient HttpError."""
    import json as _json

    try:
        body = _json.loads(exc.content.decode("utf-8"))
        err = body.get("error", {})
        return {
            "message": err.get("message", str(exc)),
            "code": exc.resp.status,
            "details": err.get("errors", None),
        }
    except Exception:
        return {"message": str(exc), "code": getattr(exc, "resp", {}).get("status"), "details": None}


def handle_api_errors(fn: Callable) -> Callable:
    """Decorator that catches common API errors and returns a ``failure()`` envelope."""
    from analytics_mcp.tools._helpers import failure

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except asyncio.TimeoutError:
            return failure("Request timed out", code=408)
        except Exception as exc:
            # GA protobuf errors
            try:
                from google.api_core.exceptions import GoogleAPICallError

                if isinstance(exc, GoogleAPICallError):
                    return failure(str(exc), code=exc.code)
            except ImportError:
                pass

            # GSC REST errors
            try:
                from googleapiclient.errors import HttpError

                if isinstance(exc, HttpError):
                    info = _parse_gsc_http_error(exc)
                    return failure(**info)
            except ImportError:
                pass

            # Auth errors
            try:
                from google.auth.exceptions import DefaultCredentialsError

                if isinstance(exc, DefaultCredentialsError):
                    return failure(
                        "Authentication failed. Set GOOGLE_SERVICE_ACCOUNT_PATH or "
                        "GOOGLE_APPLICATION_CREDENTIALS to your service-account JSON file.",
                        code=401,
                    )
            except ImportError:
                pass

            # Fallback
            return failure(str(exc))

    return wrapper
