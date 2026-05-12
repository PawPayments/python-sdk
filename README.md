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
