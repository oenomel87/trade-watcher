"""현재가 조회 API 샘플 테스트."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.stock_current_price_service import StockCurrentPriceService  # noqa: E402
from db import Database  # noqa: E402


class FakeKISClient:
    """KIS 클라이언트 테스트 더블."""

    def __init__(self, responses: dict[str, dict]):
        self.responses = responses
        self.calls: list[str] = []

    def get_current_price(
        self,
        stock_code: str,
        market: str = "J",
    ) -> dict:
        self.calls.append(stock_code)
        return self.responses[stock_code]


def test_current_price_cache_flow():
    responses = {
        "005930": {
            "rt_cd": "0",
            "output": {
                "stck_prpr": "72000",
                "prdy_vrss": "500",
                "prdy_ctrt": "0.70",
                "acml_vol": "1500000",
            },
        }
    }

    db = Database(":memory:")
    client = FakeKISClient(responses)
    service = StockCurrentPriceService(db=db, client=client)

    result = service.get_current_price(
        stock_code="005930",
        market="J",
        use_cache=True,
    )

    assert result["source"] == "kis"
    assert result["price"]["stck_prpr"] == "72000"
    assert client.calls == ["005930"]

    cached = service.get_current_price(
        stock_code="005930",
        market="J",
        use_cache=True,
    )

    assert cached["source"] == "db"
    assert cached["price"]["stck_prpr"] == "72000"
    assert client.calls == ["005930"]
