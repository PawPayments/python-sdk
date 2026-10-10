# PawPayments — Python SDK

Official Python SDK for the [PawPayments](https://pawpayments.com) Native V2 API.
Ships both a synchronous client (`PawPayments`, built on `requests`) and an
asynchronous one (`AsyncPawPayments`, built on `httpx`).

## Install

```bash
pip install pawpayments
```

Requires Python **3.9+**.

## Quickstart (sync)

```python
from pawpayments import PawPayments

paw = PawPayments(api_key="…")

invoice = paw.invoices.create(
    amount=25,
    fiat_currency="USD",
    billing_type="STATIC",
    asset="usdt_tron",
    description="Pro plan, 1 month",
    notify_url="https://example.com/paw/webhook",
)
print(invoice["payment_url"])
```

## Quickstart (async)

```python
import asyncio
from pawpayments import AsyncPawPayments


async def main():
    async with AsyncPawPayments(api_key="…") as paw:
        invoice = await paw.invoices.create(
            amount=25,
            fiat_currency="USD",
            billing_type="STATIC",
            asset="usdt_tron",
        )
        print(invoice["payment_url"])


asyncio.run(main())
```

## Resources

| Group | Methods |
|-------|---------|
| `paw.assets` | `list()` |
| `paw.rates` | `get(base=, assets=)` |
| `paw.balance` | `get()` |
| `paw.invoices` | `create(**)`, `get(id)`, `list(**)`, `notify(id)` |
| `paw.payouts` | `create(**, uniq_id=)`, `get(id)`, `list(**)`, `batch(items, uniq_id=)` |
| `paw.ledger` | `list(type=, ...)` |
| `paw.notifications` | `list(**)`, `test(url=)` |
| `paw.permanent` | `create(**)`, `get(id)`, `list(**)`, `deactivate(id)` |

`payouts.create` and `payouts.batch` accept an optional `uniq_id` for explicit
idempotency (UUIDv4). When omitted the SDK generates one with `uuid.uuid4()`.
A repeated `uniq_id` within 2 hours yields a 409.
Payout requests use `address`. Invoice responses expose `address_to` and may
include `address_from`.

Each payout (and each batch item) accepts an optional `fee_bearer` of
`"merchant"` or `"client"` to choose who covers the network fee — defaults to
`"merchant"`:

```python
paw.payouts.create(
    address="T…",
    amount=50,
    fiat_currency="USD",
    asset="usdt_tron",
    fee_bearer="client",
)
```

## Webhook verification

```python
from flask import Flask, request, abort
from pawpayments import Webhook

app = Flask(__name__)


@app.post("/paw/webhook")
def webhook():
    raw = request.get_data()
    sig = request.headers.get("X-Paw-Signature", "")
    if not Webhook.verify_raw_body(raw, sig, API_KEY):
        abort(401)
    payload = Webhook.parse_payload(raw)
    # …handle the invoice update…
    return "", 200
```

Verification always fails (returns `False`, never raises) for an empty API key
or a header that is not exactly 64 hex characters, so an unconfigured
integration never accepts a webhook.

Before settling an order on a `success` / `paid_over` webhook, check that it
pays that order: `Webhook.covers_amount(payload, order_currency, order_total)`
requires the order's currency and an invoice issued (`initial_fiat_amount`) for
at least the order total, give or take a cent. Whether enough arrived is the
gateway's call — it sends `success` only within the underpay tolerance you
configured — so a slightly short `fiat_amount` still settles the order, while a
webhook for some other, cheaper invoice whose `extra` names it never does.

## Errors

```python
from pawpayments import PawPaymentsApiError

try:
    paw.invoices.create(...)
except PawPaymentsApiError as exc:
    print(exc.code, exc.http_status, str(exc), exc.details)
```

## Testing

- `pytest tests/test_webhook.py` — signature unit tests + PHP-interop parity.
- `PAW_API_KEY=… pytest tests/test_live.py tests/test_negative.py` — live happy-path + negative-case suites against `https://api.pawpayments.com`. Tests skip when `PAW_API_KEY` is absent.

## License

MIT
