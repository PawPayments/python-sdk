import os

import pytest

from pawpayments import PawPayments, PawPaymentsApiError

API_KEY = os.environ.get("PAW_API_KEY")
BASE = os.environ.get("PAW_BASE", "https://api.pawpayments.com")

pytestmark = pytest.mark.skipif(not API_KEY, reason="PAW_API_KEY not set")


@pytest.fixture
def client():
    with PawPayments(api_key=API_KEY, base_url=BASE) as c:
        yield c


def test_bad_api_key_returns_4xx():
    with PawPayments(api_key="definitely-not-valid", base_url=BASE) as bad:
        with pytest.raises(PawPaymentsApiError) as exc:
            bad.balance.get()
        assert exc.value.http_status is not None
        assert 400 <= exc.value.http_status < 500


def test_invoices_create_empty_body_rejected(client):
    with pytest.raises(PawPaymentsApiError) as exc:
        client.invoices.create()
    assert 400 <= (exc.value.http_status or 0) < 500


def test_invoices_create_unknown_asset_rejected(client):
    with pytest.raises(PawPaymentsApiError) as exc:
        client.invoices.create(
            amount=5,
            fiat_currency="USD",
            billing_type="STATIC",
            asset="doge_doge",
        )
    assert 400 <= (exc.value.http_status or 0) < 500


def test_invoices_create_negative_amount_rejected(client):
    with pytest.raises(PawPaymentsApiError) as exc:
        client.invoices.create(
            amount=-1,
            fiat_currency="USD",
            billing_type="STATIC",
            asset="usdt_tron",
        )
    assert 400 <= (exc.value.http_status or 0) < 500


def test_invoices_get_unknown_id(client):
    with pytest.raises(PawPaymentsApiError) as exc:
        client.invoices.get("ffffffffffffffffffffffff")
    assert 400 <= (exc.value.http_status or 0) < 500


def test_payout_without_balance_or_ip(client):
    with pytest.raises(PawPaymentsApiError) as exc:
        client.payouts.create(
            address="TTestAddress1234567890",
            amount=10,
            fiat_currency="USD",
            asset="usdt_tron",
        )
    assert 400 <= (exc.value.http_status or 0) < 500


def test_payouts_get_unknown_id(client):
    with pytest.raises(PawPaymentsApiError) as exc:
        client.payouts.get("ffffffffffffffffffffffff")
    assert 400 <= (exc.value.http_status or 0) < 500


def test_permanent_create_bad_family(client):
    with pytest.raises(PawPaymentsApiError) as exc:
        client.permanent.create(user_id="live-test-user", family="not_a_family")
    assert 400 <= (exc.value.http_status or 0) < 500
