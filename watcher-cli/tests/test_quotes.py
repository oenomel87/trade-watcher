from datetime import datetime

import pytest

from watcher_cli.models import WatchItem
from watcher_cli.quotes import QuoteService


class FakeKISClient:
    def __init__(self):
        self.domestic_calls: list[tuple[str, str]] = []
        self.overseas_calls: list[tuple[str, str]] = []

    async def get_current_price(self, stock_code: str, market: str = "J") -> dict:
        self.domestic_calls.append((stock_code, market))
        if market == "J":
            return {
                "rt_cd": "0",
                "output": {
                    "stck_prpr": "72000",
                    "prdy_ctrt": "0.70",
                    "acml_vol": "1500000",
                },
            }
        return {
            "rt_cd": "0",
            "output": {
                "stck_prpr": "72100",
                "prdy_ctrt": "0.84",
                "acml_vol": "500000",
            },
        }

    async def get_overseas_price(self, exchange: str, symbol: str) -> dict:
        self.overseas_calls.append((exchange, symbol))
        return {
            "rt_cd": "0",
            "output": {
                "last": "214.33",
                "base": "211.95",
            },
        }


@pytest.mark.asyncio
async def test_quote_service_fetches_krx_and_nxt_for_korean_stocks():
    service = QuoteService(
        client=FakeKISClient(),
        current_time_provider=lambda: datetime(2026, 1, 26, 10, 0, 0),
    )

    quotes = await service.fetch_many([WatchItem(symbol="005930", name="삼성전자", market="KR")])

    assert len(quotes) == 1
    quote = quotes[0]
    assert quote.symbol == "005930"
    assert quote.best_price == "72000"
    assert quote.krx_price == "72000"
    assert quote.nxt_price == "72100"
    assert quote.change_rate == "0.70"


@pytest.mark.asyncio
async def test_quote_service_fetches_single_price_for_us_stocks():
    service = QuoteService(client=FakeKISClient())

    quotes = await service.fetch_many(
        [WatchItem(symbol="AAPL", name="Apple", market="US", exchange="NAS")]
    )

    assert len(quotes) == 1
    quote = quotes[0]
    assert quote.symbol == "AAPL"
    assert quote.best_price == "214.33"
    assert quote.krx_price is None
    assert quote.nxt_price is None
    assert quote.change_rate == "1.12"


class PartialFailureKISClient(FakeKISClient):
    async def get_current_price(self, stock_code: str, market: str = "J") -> dict:
        if market == "NX":
            return {"rt_cd": "1", "msg1": "NXT 실패"}
        return await super().get_current_price(stock_code, market)


@pytest.mark.asyncio
async def test_quote_service_keeps_krx_price_when_nxt_fails():
    service = QuoteService(
        client=PartialFailureKISClient(),
        current_time_provider=lambda: datetime(2026, 1, 26, 10, 0, 0),
    )

    quotes = await service.fetch_many([WatchItem(symbol="005930", name="삼성전자", market="KR")])

    quote = quotes[0]
    assert quote.best_price == "72000"
    assert quote.krx_price == "72000"
    assert quote.nxt_price is None
    assert quote.change_rate == "0.70"


class AfterMarketKISClient(FakeKISClient):
    async def get_current_price(self, stock_code: str, market: str = "J") -> dict:
        if market == "J":
            return {
                "rt_cd": "0",
                "output": {
                    "stck_prpr": "72000",
                    "prdy_ctrt": "0.70",
                    "acml_vol": "1500000",
                },
            }
        return {
            "rt_cd": "0",
            "output": {
                "stck_prpr": "72100",
                "prdy_ctrt": "0.84",
                "acml_vol": "500000",
            },
        }


@pytest.mark.asyncio
async def test_quote_service_prefers_nxt_when_only_nxt_is_open():
    service = QuoteService(
        client=AfterMarketKISClient(),
        current_time_provider=lambda: datetime(2026, 1, 26, 16, 0, 0),
    )

    quotes = await service.fetch_many([WatchItem(symbol="005930", name="삼성전자", market="KR")])

    quote = quotes[0]
    assert quote.best_price == "72100"
    assert quote.krx_price == "72000"
    assert quote.nxt_price == "72100"
    assert quote.change_rate == "0.84"
