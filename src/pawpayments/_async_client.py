"""Asynchronous client built on `httpx.AsyncClient`."""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

import httpx

from . import _resources as R
from ._http import base_headers, decode_envelope, unwrap_list, unwrap_result
from ._models import ListResult
from .errors import PawPaymentsApiError


class _AsyncResource:
    def __init__(self, client: "AsyncPawPayments") -> None:
        self._client = client


class _AsyncAssets(_AsyncResource):
    async def list(self) -> list[dict[str, Any]]:
        return await self._client._dispatch(R.assets_list())


class _AsyncRates(_AsyncResource):
    async def get(self, *, base: str = "USD", assets: Optional[Iterable[str] | str] = None) -> dict[str, Any]:
        return await self._client._dispatch(R.rates_get(base=base, assets=assets))


class _AsyncBalance(_AsyncResource):
    async def get(self) -> dict[str, Any]:
        return await self._client._dispatch(R.balance_get())


class _AsyncInvoices(_AsyncResource):
    async def create(self, **params: Any) -> dict[str, Any]:
        return await self._client._dispatch(R.invoices_create(params))

    async def get(self, order_id: str) -> dict[str, Any]:
        return await self._client._dispatch(R.invoices_get(order_id))

    async def list(self, **params: Any) -> ListResult:
        return await self._client._dispatch_list(R.invoices_list(**params))

    async def notify(self, order_id: str) -> dict[str, Any]:
        return await self._client._dispatch(R.invoices_notify(order_id))


class _AsyncPayouts(_AsyncResource):
    async def create(self, *, uniq_id: Optional[str] = None, **params: Any) -> dict[str, Any]:
        return await self._client._dispatch(R.payouts_create(params, uniq_id=uniq_id))

    async def batch(self, items: list[Mapping[str, Any]], *, uniq_id: Optional[str] = None) -> dict[str, Any]:
        return await self._client._dispatch(R.payouts_batch(items, uniq_id=uniq_id))

    async def get(self, payout_id: str) -> dict[str, Any]:
        return await self._client._dispatch(R.payouts_get(payout_id))

    async def list(self, **params: Any) -> ListResult:
        return await self._client._dispatch_list(R.payouts_list(**params))


class _AsyncLedger(_AsyncResource):
    async def list(self, **params: Any) -> ListResult:
        return await self._client._dispatch_list(R.ledger_list(**params))


class _AsyncNotifications(_AsyncResource):
    async def list(self, **params: Any) -> ListResult:
        return await self._client._dispatch_list(R.notifications_list(**params))

    async def test(self, url: Optional[str] = None) -> dict[str, Any]:
        return await self._client._dispatch(R.notifications_test(url))


class _AsyncPermanent(_AsyncResource):
    async def create(self, **params: Any) -> dict[str, Any]:
        return await self._client._dispatch(R.permanent_create(params))

    async def get(self, address_id: str) -> dict[str, Any]:
        return await self._client._dispatch(R.permanent_get(address_id))

    async def list(self, **params: Any) -> ListResult:
        return await self._client._dispatch_list(R.permanent_list(**params))

    async def deactivate(self, address_id: str) -> dict[str, Any]:
        return await self._client._dispatch(R.permanent_deactivate(address_id))


class AsyncPawPayments:
    """Asynchronous PawPayments client (built on `httpx.AsyncClient`)."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.pawpayments.com",
        timeout: float = 30.0,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._owns_client = client is None

        self.assets = _AsyncAssets(self)
        self.rates = _AsyncRates(self)
        self.balance = _AsyncBalance(self)
        self.invoices = _AsyncInvoices(self)
        self.payouts = _AsyncPayouts(self)
        self.ledger = _AsyncLedger(self)
        self.notifications = _AsyncNotifications(self)
        self.permanent = _AsyncPermanent(self)

    @property
    def base_url(self) -> str:
        return self._base_url

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncPawPayments":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def _dispatch(self, spec: R.RequestSpec) -> Any:
        envelope = await self._send(spec)
        return unwrap_result(envelope)

    async def _dispatch_list(self, spec: R.RequestSpec) -> ListResult:
        envelope = await self._send(spec)
        return unwrap_list(envelope)  # type: ignore[return-value]

    async def _send(self, spec: R.RequestSpec) -> dict[str, Any]:
        url = self._base_url + spec.path
        headers = base_headers(self._api_key, spec.uniq_id)
        kwargs: dict[str, Any] = {"headers": headers, "timeout": self._timeout}
        if spec.query:
            kwargs["params"] = spec.query
        if spec.body is not None:
            kwargs["json"] = spec.body
        try:
            response = await self._client.request(spec.method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise PawPaymentsApiError(
                f"Network error: {exc}", "NETWORK_ERROR", None
            ) from exc
        return decode_envelope(response.status_code, response.content or b"")
