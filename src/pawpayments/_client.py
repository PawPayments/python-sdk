"""Synchronous client built on `requests`."""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

import requests

from . import _resources as R
from ._http import base_headers, decode_envelope, unwrap_list, unwrap_result
from ._models import ListResult
from .errors import PawPaymentsApiError


class _Resource:
    def __init__(self, client: "PawPayments") -> None:
        self._client = client


class _Assets(_Resource):
    def list(self) -> list[dict[str, Any]]:
        return self._client._dispatch(R.assets_list())


class _Rates(_Resource):
    def get(self, *, base: str = "USD", assets: Optional[Iterable[str] | str] = None) -> dict[str, Any]:
        return self._client._dispatch(R.rates_get(base=base, assets=assets))


class _Balance(_Resource):
    def get(self) -> dict[str, Any]:
        return self._client._dispatch(R.balance_get())


class _Invoices(_Resource):
    def create(self, **params: Any) -> dict[str, Any]:
        return self._client._dispatch(R.invoices_create(params))

    def get(self, order_id: str) -> dict[str, Any]:
        return self._client._dispatch(R.invoices_get(order_id))

    def list(self, **params: Any) -> ListResult:
        return self._client._dispatch_list(R.invoices_list(**params))

    def notify(self, order_id: str) -> dict[str, Any]:
        return self._client._dispatch(R.invoices_notify(order_id))


class _Payouts(_Resource):
    def create(self, *, uniq_id: Optional[str] = None, **params: Any) -> dict[str, Any]:
        return self._client._dispatch(R.payouts_create(params, uniq_id=uniq_id))

    def batch(self, items: list[Mapping[str, Any]], *, uniq_id: Optional[str] = None) -> dict[str, Any]:
        return self._client._dispatch(R.payouts_batch(items, uniq_id=uniq_id))

    def get(self, payout_id: str) -> dict[str, Any]:
        return self._client._dispatch(R.payouts_get(payout_id))

    def list(self, **params: Any) -> ListResult:
        return self._client._dispatch_list(R.payouts_list(**params))


class _Ledger(_Resource):
    def list(self, **params: Any) -> ListResult:
        return self._client._dispatch_list(R.ledger_list(**params))


class _Notifications(_Resource):
    def list(self, **params: Any) -> ListResult:
        return self._client._dispatch_list(R.notifications_list(**params))

    def test(self, url: Optional[str] = None) -> dict[str, Any]:
        return self._client._dispatch(R.notifications_test(url))


class _Permanent(_Resource):
    def create(self, **params: Any) -> dict[str, Any]:
        return self._client._dispatch(R.permanent_create(params))

    def get(self, address_id: str) -> dict[str, Any]:
        return self._client._dispatch(R.permanent_get(address_id))

    def list(self, **params: Any) -> ListResult:
        return self._client._dispatch_list(R.permanent_list(**params))

    def deactivate(self, address_id: str) -> dict[str, Any]:
        return self._client._dispatch(R.permanent_deactivate(address_id))


class PawPayments:
    """Synchronous PawPayments client (built on `requests`)."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.pawpayments.com",
        timeout: float = 30.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session or requests.Session()
        self._owns_session = session is None

        self.assets = _Assets(self)
        self.rates = _Rates(self)
        self.balance = _Balance(self)
        self.invoices = _Invoices(self)
        self.payouts = _Payouts(self)
        self.ledger = _Ledger(self)
        self.notifications = _Notifications(self)
        self.permanent = _Permanent(self)

    @property
    def base_url(self) -> str:
        return self._base_url

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def __enter__(self) -> "PawPayments":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _dispatch(self, spec: R.RequestSpec) -> Any:
        envelope = self._send(spec)
        return unwrap_result(envelope)

    def _dispatch_list(self, spec: R.RequestSpec) -> ListResult:
        envelope = self._send(spec)
        return unwrap_list(envelope)  # type: ignore[return-value]

    def _send(self, spec: R.RequestSpec) -> dict[str, Any]:
        url = self._base_url + spec.path
        headers = base_headers(self._api_key, spec.uniq_id)
        kwargs: dict[str, Any] = {"headers": headers, "timeout": self._timeout}
        if spec.query:
            kwargs["params"] = spec.query
        if spec.body is not None:
            kwargs["json"] = spec.body
        try:
            response = self._session.request(spec.method, url, **kwargs)
        except requests.RequestException as exc:
            raise PawPaymentsApiError(
                f"Network error: {exc}", "NETWORK_ERROR", None
            ) from exc
        return decode_envelope(response.status_code, response.content or b"")
