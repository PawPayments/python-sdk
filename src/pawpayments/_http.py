"""Shared envelope/error decoding used by both sync and async transports."""
from __future__ import annotations

import json
from typing import Any, Optional

from .errors import PawPaymentsApiError

DEFAULT_USER_AGENT = "pawpayments-python-sdk/0.1.0"


def base_headers(api_key: str, uniq_id: Optional[str] = None) -> dict[str, str]:
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
        "User-Agent": DEFAULT_USER_AGENT,
    }
    if uniq_id:
        headers["x-uniq-id"] = uniq_id
    return headers


def decode_envelope(status: int, raw: bytes) -> dict[str, Any]:
    if not raw:
        if status >= 400:
            raise PawPaymentsApiError(f"HTTP {status}", "UNKNOWN", status)
        return {}
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PawPaymentsApiError(
            f"Invalid JSON response (HTTP {status})", "INVALID_RESPONSE", status
        ) from exc
    if not isinstance(decoded, dict):
        raise PawPaymentsApiError(
            f"Invalid JSON response (HTTP {status})", "INVALID_RESPONSE", status
        )
    if status >= 400 or decoded.get("ok") is False:
        err = decoded.get("error")
        if isinstance(err, dict):
            code = str(err.get("code") or "UNKNOWN")
            message = str(err.get("message") or f"HTTP {status}")
            details = err.get("details") if isinstance(err.get("details"), list) else None
        else:
            code = str(decoded.get("code") or err or "UNKNOWN")
            message = str(decoded.get("message") or err or f"HTTP {status}")
            details = None
        raise PawPaymentsApiError(message, code, status, details)
    return decoded


def unwrap_result(envelope: dict[str, Any]) -> Any:
    if "result" in envelope:
        return envelope["result"]
    if "data" in envelope:
        return envelope["data"]
    return envelope


def unwrap_list(envelope: dict[str, Any]) -> dict[str, Any]:
    items = envelope.get("result")
    if items is None:
        items = envelope.get("data") or []
    if not isinstance(items, list):
        items = []
    pagination = envelope.get("pagination") or {
        "page": 1,
        "per_page": len(items),
        "total": len(items),
        "pages": 1,
    }
    return {"items": items, "pagination": pagination}
