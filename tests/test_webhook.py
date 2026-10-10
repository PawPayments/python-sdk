import hashlib
import hmac
import shutil
import subprocess

import pytest

from pawpayments import Webhook

API_KEY = "test_api_key_abc123"


def _sig(message: bytes | str) -> str:
    if isinstance(message, str):
        message = message.encode()
    return hmac.new(API_KEY.encode(), message, hashlib.sha256).hexdigest()


def test_verify_raw_body_valid():
    body = '{"order_id":"abc","status":"success"}'
    assert Webhook.verify_raw_body(body, _sig(body), API_KEY) is True


def test_verify_raw_body_bad_signature():
    body = '{"order_id":"abc","status":"success"}'
    assert Webhook.verify_raw_body(body, "deadbeef", API_KEY) is False


def test_verify_raw_body_tampered():
    body = '{"order_id":"abc","status":"success"}'
    sig = _sig(body)
    assert Webhook.verify_raw_body('{"order_id":"abc","status":"cancelled"}', sig, API_KEY) is False


def test_verify_raw_body_bytes_input():
    body = '{"order_id":"abc"}'
    assert Webhook.verify_raw_body(body.encode(), _sig(body), API_KEY) is True


def test_verify_raw_body_empty_signature():
    assert Webhook.verify_raw_body("{}", "", API_KEY) is False


def test_verify_raw_body_empty_api_key():
    body = '{"order_id":"abc"}'
    sig = hmac.new(b"", body.encode(), hashlib.sha256).hexdigest()
    assert Webhook.verify_raw_body(body, sig, "") is False


def test_verify_raw_body_uppercase_hex_accepted():
    body = '{"order_id":"abc"}'
    assert Webhook.verify_raw_body(body, _sig(body).upper(), API_KEY) is True


@pytest.mark.parametrize(
    "mangle",
    [
        lambda s: s[:63],
        lambda s: s + "0",
        lambda s: s + "\n",
        lambda s: "g" * 64,
    ],
)
def test_verify_raw_body_malformed_header(mangle):
    body = '{"order_id":"abc"}'
    assert Webhook.verify_raw_body(body, mangle(_sig(body)), API_KEY) is False


def test_verify_raw_body_non_ascii_header_returns_false():
    body = '{"order_id":"abc"}'
    assert Webhook.verify_raw_body(body, "é" * 64, API_KEY) is False
    assert Webhook.verify_raw_body(body, _sig(body)[:63] + "é", API_KEY) is False


def test_parse_payload_object():
    body = '{"order_id":"abc","status":"success","amount":100.5}'
    payload = Webhook.parse_payload(body)
    assert payload["order_id"] == "abc"
    assert payload["amount"] == 100.5


def test_parse_payload_invalid_json():
    with pytest.raises(ValueError):
        Webhook.parse_payload("not json")


def test_parse_payload_array_rejected():
    with pytest.raises(ValueError):
        Webhook.parse_payload("[1,2,3]")


@pytest.mark.skipif(shutil.which("php") is None, reason="PHP not installed")
def test_php_interop_round_trip(tmp_path):
    """PHP `Webhook::verifyRawBody` from the official PHP SDK must accept
    our Python-generated signature unchanged."""
    body = '{"order_id":"abc","status":"success"}'
    sig = _sig(body)
    php_code = (
        "$body = file_get_contents($argv[1]);"
        "$expected = hash_hmac('sha256', $body, $argv[3]);"
        "echo hash_equals($expected, $argv[2]) ? 'OK' : 'BAD';"
    )
    body_file = tmp_path / "body.json"
    body_file.write_text(body)
    proc = subprocess.run(
        ["php", "-r", php_code, str(body_file), sig, API_KEY],
        capture_output=True,
        timeout=5,
    )
    assert proc.stdout.strip() == b"OK", proc.stdout + proc.stderr


def test_covers_amount_invoice_issued_for_the_total():
    payload = {"initial_fiat_amount": 100.0, "fiat_amount": 100.0, "fiat_currency": "USD"}
    assert Webhook.covers_amount(payload, "USD", 100)
    assert Webhook.covers_amount(payload, "usd", "100.00")
    assert Webhook.covers_amount({**payload, "fiat_currency": "usd"}, "USD", 100)


def test_covers_amount_trusts_the_gateways_own_tolerance():
    # A merchant may accept 20% short; the gateway then sends `success` with 80.
    payload = {"initial_fiat_amount": "100", "fiat_amount": "80", "fiat_currency": "EUR"}
    assert Webhook.covers_amount(payload, "EUR", 100)


def test_covers_amount_refuses_a_webhook_for_a_cheaper_invoice():
    payload = {"initial_fiat_amount": 1.0, "fiat_amount": 1.0, "fiat_currency": "USD"}
    assert not Webhook.covers_amount(payload, "USD", 500)


def test_covers_amount_allows_only_a_cent_of_rounding():
    assert Webhook.covers_amount({"initial_fiat_amount": 99.99, "fiat_currency": "USD"}, "USD", 100)
    assert not Webhook.covers_amount({"initial_fiat_amount": 99.98, "fiat_currency": "USD"}, "USD", 100)
    assert Webhook.covers_amount({"initial_fiat_amount": 120, "fiat_currency": "USD"}, "USD", 100)


def test_covers_amount_refuses_another_or_a_missing_currency():
    assert not Webhook.covers_amount({"initial_fiat_amount": 100000, "fiat_currency": "IDR"}, "USD", 100)
    assert not Webhook.covers_amount({"initial_fiat_amount": 100}, "USD", 100)
    assert not Webhook.covers_amount({"initial_fiat_amount": 100, "fiat_currency": "USD"}, "", 100)
    # Unknown on both sides is not a match.
    assert not Webhook.covers_amount({"initial_fiat_amount": 100}, "", 100)


@pytest.mark.parametrize("issued", [None, "x", "", True, float("nan"), float("inf")])
def test_covers_amount_refuses_a_payload_without_a_usable_issued_amount(issued):
    payload = {"fiat_amount": 100, "fiat_currency": "USD"}
    if issued is not None:
        payload["initial_fiat_amount"] = issued
    assert not Webhook.covers_amount(payload, "USD", 100)


@pytest.mark.parametrize("total", [None, "", "abc", float("nan")])
def test_covers_amount_refuses_a_total_that_is_not_a_number(total):
    assert not Webhook.covers_amount({"initial_fiat_amount": 100, "fiat_currency": "USD"}, "USD", total)
