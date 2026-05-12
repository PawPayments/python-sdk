"""Route specifications shared between the sync and async clients.

Each resource method builds a ``RequestSpec`` describing how to call the
HTTP API. The two transport implementations (`_client.PawPayments` and
`_async_client.AsyncPawPayments`) wire the spec into their respective
HTTP libraries so we don't repeat URL/query/body wiring twice.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional


@dataclass
class RequestSpec:
    method: str
    path: str
    query: dict[str, Any] = field(default_factory=dict)
    body: Optional[Any] = None
    uniq_id: Optional[str] = None
    paginated: bool = False


def _drop_none(d: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _join(value: Any) -> Any:
    if isinstance(value, (list, tuple, set)) and not isinstance(value, str):
        return ",".join(str(v) for v in value)
    return value


def assets_list() -> RequestSpec:
    return RequestSpec("GET", "/api/v2/assets")


def rates_get(*, base: str = "USD", assets: Optional[Iterable[str] | str] = None) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/api/v2/rates",
        query=_drop_none({"base": base, "assets": _join(assets) if assets else None}),
    )


def balance_get() -> RequestSpec:
    return RequestSpec("GET", "/api/v2/balance")


def invoices_create(params: Mapping[str, Any]) -> RequestSpec:
    return RequestSpec("POST", "/api/v2/invoices", body=dict(params))


def invoices_get(order_id: str) -> RequestSpec:
    return RequestSpec("GET", f"/api/v2/invoices/{order_id}")


def invoices_list(**params: Any) -> RequestSpec:
    if "order_ids" in params:
        params["order_ids"] = _join(params["order_ids"])
    return RequestSpec("GET", "/api/v2/invoices", query=_drop_none(params), paginated=True)


def invoices_notify(order_id: str) -> RequestSpec:
    return RequestSpec("POST", f"/api/v2/invoices/{order_id}/notify")


def payouts_create(params: Mapping[str, Any], uniq_id: Optional[str] = None) -> RequestSpec:
    return RequestSpec(
        "POST",
        "/api/v2/payouts",
        body=dict(params),
        uniq_id=uniq_id or str(uuid.uuid4()),
    )


def payouts_batch(items: list[Mapping[str, Any]], uniq_id: Optional[str] = None) -> RequestSpec:
    return RequestSpec(
        "POST",
        "/api/v2/payouts/batch",
        body={"items": [dict(i) for i in items]},
        uniq_id=uniq_id or str(uuid.uuid4()),
    )


def payouts_get(payout_id: str) -> RequestSpec:
    return RequestSpec("GET", f"/api/v2/payouts/{payout_id}")


def payouts_list(**params: Any) -> RequestSpec:
    if "order_ids" in params:
        params["order_ids"] = _join(params["order_ids"])
    return RequestSpec("GET", "/api/v2/payouts", query=_drop_none(params), paginated=True)


def ledger_list(**params: Any) -> RequestSpec:
    return RequestSpec("GET", "/api/v2/ledger", query=_drop_none(params), paginated=True)


def notifications_list(**params: Any) -> RequestSpec:
    return RequestSpec("GET", "/api/v2/notifications", query=_drop_none(params), paginated=True)


def notifications_test(url: Optional[str] = None) -> RequestSpec:
    return RequestSpec("POST", "/api/v2/notifications/test", body={"url": url} if url else {})


def permanent_create(params: Mapping[str, Any]) -> RequestSpec:
    return RequestSpec("POST", "/api/v2/permanent", body=dict(params))


def permanent_get(address_id: str) -> RequestSpec:
    return RequestSpec("GET", f"/api/v2/permanent/{address_id}")


def permanent_list(**params: Any) -> RequestSpec:
    return RequestSpec("GET", "/api/v2/permanent", query=_drop_none(params), paginated=True)


def permanent_deactivate(address_id: str) -> RequestSpec:
    return RequestSpec("DELETE", f"/api/v2/permanent/{address_id}")
