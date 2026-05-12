import os

import pytest

from pawpayments import AsyncPawPayments, PawPayments

API_KEY = os.environ.get("PAW_API_KEY")
BASE = os.environ.get("PAW_BASE", "https://api.pawpayments.com")

pytestmark = pytest.mark.skipif(not API_KEY, reason="PAW_API_KEY not set")


@pytest.fixture
def client():
    with PawPayments(api_key=API_KEY, base_url=BASE) as c:
        yield c


@pytest.fixture
async def async_client():
    async with AsyncPawPayments(api_key=API_KEY, base_url=BASE) as c:
        yield c


def test_assets_list(client):
    assets = client.assets.list()
    assert isinstance(assets, list)
    assert assets
    assert any(a.get("enabled", True) for a in assets)


def test_rates_get(client):
    rates = client.rates.get(base="USD")
    assert rates["base"] == "USD"
    assert isinstance(rates["rates"], dict)
    assert rates["rates"]


def test_balance_get(client):
    balance = client.balance.get()
    assert isinstance(balance, dict)


def test_invoices_create_get_list(client):
    invoice = client.invoices.create(
        amount=25,
        fiat_currency="USD",
        billing_type="STATIC",
        asset="usdt_tron",
        description="Python SDK live test",
        ttl=1800,
    )
    assert invoice["order_id"]
    fetched = client.invoices.get(invoice["order_id"])
    assert fetched["order_id"] == invoice["order_id"]
    page = client.invoices.list(page=1, per_page=5)
    assert page["pagination"]["page"] == 1
    assert isinstance(page["items"], list)


def test_payouts_list_readonly(client):
    page = client.payouts.list(page=1, per_page=5)
    assert page["pagination"]["page"] == 1
    assert isinstance(page["items"], list)


def test_ledger_list(client):
    page = client.ledger.list(page=1, per_page=5)
    assert page["pagination"]["page"] == 1


def test_notifications_list(client):
    page = client.notifications.list(page=1, per_page=5)
    assert isinstance(page["items"], list)


def test_notifications_test_probe(client):
    probe = client.notifications.test("https://httpbin.org/status/200")
    assert probe["url"] == "https://httpbin.org/status/200"
    assert "delivered" in probe


def test_permanent_list(client):
    page = client.permanent.list(page=1, per_page=5)
    assert page["pagination"]["page"] == 1


async def test_async_assets_list(async_client):
    assets = await async_client.assets.list()
    assert isinstance(assets, list)
    assert assets


async def test_async_invoices_round_trip(async_client):
    invoice = await async_client.invoices.create(
        amount=15,
        fiat_currency="USD",
        billing_type="STATIC",
        asset="usdt_tron",
        description="Async Python SDK live test",
        ttl=1800,
    )
    assert invoice["order_id"]
    fetched = await async_client.invoices.get(invoice["order_id"])
    assert fetched["order_id"] == invoice["order_id"]
