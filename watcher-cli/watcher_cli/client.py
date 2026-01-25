"""HTTP client for watcher-engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from watcher_cli.models import (
    CurrentPriceResponse,
    PeriodicPriceResponse,
    Stock,
    Watchlist,
    WatchlistCreateResponse,
    WatchlistDetail,
    WatchlistFolder,
    WatchlistItemCreateResult,
    WatchlistItemSummary,
)


@dataclass
class EngineAPIError(Exception):
    message: str
    status_code: int | None = None
    response: Any | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        return " (".join(parts) + (")" if len(parts) > 1 else "")


class EngineClient:
    """Async client for watcher-engine APIs."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def __aenter__(self) -> "EngineClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def list_watchlists(self) -> list[Watchlist]:
        payload = await self._request("GET", "/watchlists")
        items = payload.get("watchlists", []) if isinstance(payload, dict) else []
        return [Watchlist.model_validate(item) for item in items]

    async def create_watchlist(self, name: str, description: str | None = None) -> WatchlistCreateResponse:
        params: dict[str, Any] = {"name": name}
        if description:
            params["description"] = description
        payload = await self._request("POST", "/watchlists", params=params)
        return WatchlistCreateResponse.model_validate(payload)

    async def delete_watchlist(self, watchlist_id: int) -> None:
        await self._request("DELETE", f"/watchlists/{watchlist_id}")

    async def get_watchlist(
        self,
        watchlist_id: int,
        include_folders: bool = True,
        include_items: bool = False,
    ) -> WatchlistDetail:
        payload = await self._request(
            "GET",
            f"/watchlists/{watchlist_id}",
            params={
                "include_folders": include_folders,
                "include_items": include_items,
            },
        )
        return WatchlistDetail.model_validate(payload)

    async def list_folders(self, watchlist_id: int) -> list[WatchlistFolder]:
        payload = await self._request("GET", f"/watchlists/{watchlist_id}/folders")
        items = payload.get("folders", []) if isinstance(payload, dict) else []
        return [WatchlistFolder.model_validate(item) for item in items]

    async def create_folder(
        self,
        watchlist_id: int,
        name: str,
        description: str | None = None,
    ) -> WatchlistFolder:
        params: dict[str, Any] = {"name": name}
        if description:
            params["description"] = description
        payload = await self._request("POST", f"/watchlists/{watchlist_id}/folders", params=params)
        return WatchlistFolder.model_validate(payload)

    async def update_folder(
        self,
        watchlist_id: int,
        folder_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> WatchlistFolder:
        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
        payload = await self._request(
            "PATCH",
            f"/watchlists/{watchlist_id}/folders/{folder_id}",
            params=params,
        )
        return WatchlistFolder.model_validate(payload)

    async def delete_folder(self, watchlist_id: int, folder_id: int) -> None:
        await self._request("DELETE", f"/watchlists/{watchlist_id}/folders/{folder_id}")

    async def list_items_summary(
        self,
        watchlist_id: int,
        folder_id: int | None = None,
        use_cache: bool = True,
        max_age_sec: int | None = None,
        refresh_missing: bool = False,
        market: str = "J",
    ) -> list[WatchlistItemSummary]:
        params: dict[str, Any] = {
            "use_cache": use_cache,
            "market": market,
            "refresh_missing": refresh_missing,
        }
        if folder_id is not None:
            params["folder_id"] = folder_id
        if max_age_sec is not None:
            params["max_age_sec"] = max_age_sec

        payload = await self._request(
            "GET",
            f"/watchlists/{watchlist_id}/items/summary",
            params=params,
        )
        items = payload.get("items", []) if isinstance(payload, dict) else []
        return [WatchlistItemSummary.model_validate(item) for item in items]

    async def add_item(
        self,
        watchlist_id: int,
        stock_code: str,
        folder_id: int | None = None,
        memo: str | None = None,
    ) -> WatchlistItemCreateResult:
        params: dict[str, Any] = {"stock_code": stock_code}
        if folder_id is not None:
            params["folder_id"] = folder_id
        if memo is not None:
            params["memo"] = memo

        payload = await self._request(
            "POST",
            f"/watchlists/{watchlist_id}/items",
            params=params,
        )
        return WatchlistItemCreateResult.model_validate(payload)

    async def delete_item(self, watchlist_id: int, item_id: int) -> None:
        await self._request("DELETE", f"/watchlists/{watchlist_id}/items/{item_id}")

    async def search_stocks(self, query: str, limit: int = 20) -> list[Stock]:
        payload = await self._request("GET", "/stocks/search", params={"q": query, "limit": limit})
        items = payload.get("stocks", []) if isinstance(payload, dict) else []
        return [Stock.model_validate(item) for item in items]

    async def get_stock(self, code: str) -> Stock:
        payload = await self._request("GET", f"/stocks/{code}")
        return Stock.model_validate(payload)

    async def get_periodic_prices(
        self,
        code: str,
        start_date: str,
        end_date: str,
        period: str = "D",
        market: str = "J",
        adj_price: bool = True,
        use_cache: bool = True,
    ) -> PeriodicPriceResponse:
        payload = await self._request(
            "GET",
            f"/stocks/{code}/prices/periodic",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "period": period,
                "market": market,
                "adj_price": adj_price,
                "use_cache": use_cache,
            },
        )
        return PeriodicPriceResponse.model_validate(payload)

    async def get_current_price(
        self,
        code: str,
        market: str = "J",
        use_cache: bool = False,
        max_age_sec: int | None = None,
    ) -> CurrentPriceResponse:
        params: dict[str, Any] = {"market": market, "use_cache": use_cache}
        if max_age_sec is not None:
            params["max_age_sec"] = max_age_sec

        payload = await self._request("GET", f"/stocks/{code}/prices/current", params=params)
        return CurrentPriceResponse.model_validate(payload)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = await self._client.request(method, path, params=params, json=json)
        except httpx.HTTPError as exc:
            raise EngineAPIError("요청에 실패했습니다", response=str(exc)) from exc

        if response.status_code >= 400:
            raise EngineAPIError(
                "엔진 응답 오류",
                status_code=response.status_code,
                response=_safe_json(response),
            )

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text
