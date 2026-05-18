from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime

from watcher_cli.kis import APIError, KISClient
from watcher_cli.models import QuoteSnapshot, WatchItem


class QuoteService:
    def __init__(
        self,
        client: KISClient | None = None,
        current_time_provider: Callable[[], datetime] | None = None,
    ):
        self.client = client or KISClient()
        self.current_time_provider = current_time_provider or datetime.now

    async def close(self) -> None:
        close = getattr(self.client, "close", None)
        if callable(close):
            await close()

    async def fetch_many(self, items: list[WatchItem]) -> list[QuoteSnapshot]:
        results = await asyncio.gather(*(self._fetch_one(item) for item in items))
        return list(results)

    async def _fetch_one(self, item: WatchItem) -> QuoteSnapshot:
        try:
            if item.market == "KR":
                return await self._fetch_korean(item)
            return await self._fetch_us(item)
        except Exception as exc:
            return QuoteSnapshot(
                symbol=item.symbol,
                name=item.name,
                market=item.market,
                best_price=None,
                krx_price=None,
                nxt_price=None,
                change_rate=None,
                error=str(exc),
            )

    async def _fetch_korean(self, item: WatchItem) -> QuoteSnapshot:
        krx_response, nxt_response = await asyncio.gather(
            self.client.get_current_price(item.symbol, market="J"),
            self.client.get_current_price(item.symbol, market="NX"),
            return_exceptions=True,
        )

        krx = self._extract_domestic_safe(krx_response)
        nxt = self._extract_domestic_safe(nxt_response)
        best = self._pick_best_market(krx, nxt, self._get_active_exchanges())

        if best["price"] is None:
            raise APIError("국내 시세 조회 실패")

        return QuoteSnapshot(
            symbol=item.symbol,
            name=item.name,
            market=item.market,
            best_price=best["price"],
            krx_price=krx["price"],
            nxt_price=nxt["price"],
            change_rate=best["change_rate"],
        )

    async def _fetch_us(self, item: WatchItem) -> QuoteSnapshot:
        exchange = item.exchange or "NAS"
        response = await self.client.get_overseas_price(exchange, item.symbol)
        if response.get("rt_cd") != "0":
            raise APIError("해외 시세 조회 실패", response=response)

        output = response.get("output", {})
        last = output.get("last")
        base = output.get("base")
        change_rate = self._calc_change_rate(last, base)

        return QuoteSnapshot(
            symbol=item.symbol,
            name=item.name,
            market=item.market,
            best_price=last,
            krx_price=None,
            nxt_price=None,
            change_rate=change_rate,
        )

    def _extract_domestic(self, response: dict) -> dict[str, str | int | None]:
        if response.get("rt_cd") != "0":
            raise APIError("국내 시세 조회 실패", response=response)
        output = response.get("output", {})
        return {
            "price": output.get("stck_prpr"),
            "change_rate": output.get("prdy_ctrt"),
            "volume": self._safe_int(output.get("acml_vol")) or 0,
        }

    def _extract_domestic_safe(
        self,
        response: dict | Exception,
    ) -> dict[str, str | int | None]:
        if isinstance(response, Exception):
            return {"price": None, "change_rate": None, "volume": 0}
        try:
            return self._extract_domestic(response)
        except APIError:
            return {"price": None, "change_rate": None, "volume": 0}

    def _pick_best_market(
        self,
        krx: dict[str, str | int | None],
        nxt: dict[str, str | int | None],
        active_exchanges: list[str],
    ) -> dict[str, str | int | None]:
        if active_exchanges == ["KRX"]:
            return krx if krx["price"] else {"price": None, "change_rate": None, "volume": 0}
        if active_exchanges == ["NXT"]:
            return nxt if nxt["price"] else {"price": None, "change_rate": None, "volume": 0}
        if krx["price"] and not nxt["price"]:
            return krx
        if nxt["price"] and not krx["price"]:
            return nxt
        if not krx["price"] and not nxt["price"]:
            return {"price": None, "change_rate": None, "volume": 0}
        if (nxt["volume"] or 0) > (krx["volume"] or 0):
            return nxt
        return krx

    def _get_active_exchanges(self) -> list[str]:
        current_time = self.current_time_provider()
        time_value = current_time.hour * 60 + current_time.minute

        nxt_pre_start = 8 * 60
        nxt_pre_end = 8 * 60 + 50
        regular_start = 9 * 60
        nxt_regular_end = 15 * 60 + 20
        krx_regular_end = 15 * 60 + 30
        nxt_post_start = 15 * 60 + 40
        nxt_post_end = 20 * 60

        if nxt_pre_start <= time_value < nxt_pre_end:
            return ["NXT"]
        if regular_start <= time_value < nxt_regular_end:
            return ["KRX", "NXT"]
        if nxt_regular_end <= time_value < krx_regular_end:
            return ["KRX"]
        if nxt_post_start <= time_value <= nxt_post_end:
            return ["NXT"]
        return []

    @staticmethod
    def _safe_int(value: str | None) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _calc_change_rate(last: str | None, base: str | None) -> str | None:
        if not last or not base:
            return None
        try:
            base_value = float(base)
            if base_value == 0:
                return None
            return f"{((float(last) - base_value) / base_value) * 100:.2f}"
        except ValueError:
            return None
