"""NXT 통합 시세 조회 테스트."""

from datetime import datetime
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.stock_current_price_service import StockCurrentPriceService  # noqa: E402
from db import Database  # noqa: E402


class FakeKISClient:
    """KIS 클라이언트 테스트 더블."""

    def __init__(self, responses: dict[tuple[str, str], dict]):
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    def get_current_price(
        self,
        stock_code: str,
        market: str = "J",
    ) -> dict:
        self.calls.append((stock_code, market))
        return self.responses.get((stock_code, market), {"rt_cd": "1", "msg1": "조회 실패"})


def test_combined_price_query():
    """KRX와 NXT 통합 시세 조회 테스트."""
    responses = {
        ("005930", "J"): {
            "rt_cd": "0",
            "output": {
                "stck_prpr": "72000",
                "prdy_vrss": "500",
                "acml_vol": "1500000",
            },
        },
        ("005930", "NX"): {
            "rt_cd": "0",
            "output": {
                "stck_prpr": "72100",
                "prdy_vrss": "600",
                "acml_vol": "500000",
            },
        },
    }

    db = Database(":memory:")
    client = FakeKISClient(responses)
    service = StockCurrentPriceService(db=db, client=client)

    result = service.get_combined_price(stock_code="005930")

    assert result["code"] == "005930"
    assert result["krx"]["price"]["stck_prpr"] == "72000"
    assert result["nxt"]["price"]["stck_prpr"] == "72100"
    # KRX가 거래량이 더 많으므로 best는 KRX
    assert result["best"]["exchange"] == "KRX"
    assert result["best"]["price"] == 72000

    # API 호출 확인 (KRX, NXT 둘 다 호출)
    assert ("005930", "J") in client.calls
    assert ("005930", "NX") in client.calls


def test_combined_price_nxt_only():
    """NXT만 거래 가능한 경우 테스트."""
    responses = {
        ("005930", "J"): {
            "rt_cd": "1",
            "msg1": "조회 실패",
        },
        ("005930", "NX"): {
            "rt_cd": "0",
            "output": {
                "stck_prpr": "72100",
                "prdy_vrss": "600",
                "acml_vol": "500000",
            },
        },
    }

    db = Database(":memory:")
    client = FakeKISClient(responses)
    service = StockCurrentPriceService(db=db, client=client)

    result = service.get_combined_price(stock_code="005930")

    assert result["krx"]["error"] is not None  # KRX 오류
    assert result["nxt"]["price"]["stck_prpr"] == "72100"
    assert result["best"]["exchange"] == "NXT"


def test_active_exchanges_pre_market():
    """장전 시간(08:30) 활성 거래소 테스트."""
    service = StockCurrentPriceService()
    pre_market_time = datetime(2026, 1, 26, 8, 30, 0)

    active = service.get_active_exchanges(pre_market_time)

    assert active == ["NXT"]


def test_active_exchanges_regular_market():
    """정규장 시간(10:00) 활성 거래소 테스트."""
    service = StockCurrentPriceService()
    regular_time = datetime(2026, 1, 26, 10, 0, 0)

    active = service.get_active_exchanges(regular_time)

    assert "KRX" in active
    assert "NXT" in active


def test_active_exchanges_after_market():
    """장후 시간(18:00) 활성 거래소 테스트."""
    service = StockCurrentPriceService()
    after_time = datetime(2026, 1, 26, 18, 0, 0)

    active = service.get_active_exchanges(after_time)

    assert active == ["NXT"]


def test_active_exchanges_closed():
    """장 마감 시간(21:00) 활성 거래소 테스트."""
    service = StockCurrentPriceService()
    closed_time = datetime(2026, 1, 26, 21, 0, 0)

    active = service.get_active_exchanges(closed_time)

    assert active == []
