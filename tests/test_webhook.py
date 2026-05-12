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
