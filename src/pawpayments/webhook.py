from __future__ import annotations

import hashlib
import hmac
import json
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Mapping, Optional, Union

_BodyT = Union[str, bytes, bytearray, memoryview]

# Hex-encoded HMAC-SHA256 digest, exactly as the gateway sends it.
_SIGNATURE_RE = re.compile(r"[0-9a-fA-F]{64}")


def _to_bytes(body: _BodyT) -> bytes:
    if isinstance(body, (bytes, bytearray, memoryview)):
        return bytes(body)
    return body.encode("utf-8")


def _to_decimal(value: Any) -> Optional[Decimal]:
    """A finite amount from a JSON number or a numeric string, else None."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def _cents(amount: Decimal) -> int:
    """A fiat amount in whole cents, the unit the SDKs compare in."""
    return int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))


class Webhook:
    @staticmethod
    def verify_raw_body(raw_body: _BodyT, header_signature: str, api_key: str) -> bool:
        # An empty key makes the HMAC computable by anyone. The format check also
        # keeps non-ASCII input away from compare_digest, which raises on it.
        if (
            not api_key
            or not isinstance(header_signature, str)
            or not _SIGNATURE_RE.fullmatch(header_signature)
        ):
            return False
        expected = hmac.new(api_key.encode("utf-8"), _to_bytes(raw_body), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, header_signature.lower())

    @staticmethod
    def parse_payload(raw_body: _BodyT) -> dict[str, Any]:
        try:
            data = json.loads(_to_bytes(raw_body).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid webhook payload: not valid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("Invalid webhook payload: not valid JSON")
        return data

    @staticmethod
    def covers_amount(payload: Mapping[str, Any], currency: str, total: Any) -> bool:
        """Whether a paid (``success`` / ``paid_over``) webhook pays an amount
        you are about to settle, e.g. an order total.

        The gateway has already judged the payment against its own invoice: it
        sends ``success`` only when what arrived is within that invoice's
        underpay tolerance — whichever one the merchant configured, which the
        webhook does not carry — and ``paid_over`` when more arrived. What is
        left is to check that the invoice is for this amount: it was issued
        (``initial_fiat_amount``) for at least ``total``, in ``currency``, give
        or take a cent of rounding. So a genuine webhook for a cheaper invoice —
        one made with a stolen API key and an ``extra`` naming this order, say —
        never settles it.

        Every paid webhook the gateway sends carries ``initial_fiat_amount``; a
        payload without it is refused.
        """
        paid_currency = str(payload.get("fiat_currency") or "").upper()
        if not paid_currency or paid_currency != str(currency or "").upper():
            return False
        issued = _to_decimal(payload.get("initial_fiat_amount"))
        expected = _to_decimal(total)
        if issued is None or expected is None:
            return False
        # In whole cents, as the PHP and Node SDKs do (they work in binary
        # floats). One cent absorbs rounding of the fiat amounts on either side.
        return _cents(issued) >= _cents(expected) - 1
