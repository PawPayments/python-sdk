from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Union

_BodyT = Union[str, bytes, bytearray, memoryview]


def _to_bytes(body: _BodyT) -> bytes:
    if isinstance(body, (bytes, bytearray, memoryview)):
        return bytes(body)
    return body.encode("utf-8")


class Webhook:
    @staticmethod
    def verify_raw_body(raw_body: _BodyT, header_signature: str, api_key: str) -> bool:
        if not header_signature:
            return False
        expected = hmac.new(api_key.encode("utf-8"), _to_bytes(raw_body), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, header_signature)

    @staticmethod
    def parse_payload(raw_body: _BodyT) -> dict[str, Any]:
        try:
            data = json.loads(_to_bytes(raw_body).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid webhook payload: not valid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("Invalid webhook payload: not valid JSON")
        return data
