"""기간별 시세 API 샘플 테스트."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.stock_price_service import StockPriceService  # noqa: E402
from db import Database  # noqa: E402


class FakeKISClient:
    """KIS 클라이언트 테스트 더블."""

    def __init__(self, responses: dict[str, dict]):
        self.responses = responses
        self.calls: list[str] = []

    def get_periodic_prices(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        period: str = "D",
        adj_price: bool = True,
        market: str = "J",
    ) -> dict:
        self.calls.append(stock_code)
        return self.responses[stock_code]


def test_periodic_prices_samsung_cache():
    responses = {
        "005930": {
            "rt_cd": "0",
            "output2": [
                {
                    "stck_bsop_date": "20240102",
                    "stck_oprc": "70000",
                    "stck_hgpr": "71000",
                    "stck_lwpr": "69000",
                    "stck_clpr": "70500",
                    "acml_vol": "1000000",
                    "acml_tr_pbmn": "70000000000",
                    "flng_cls_code": "00",
                    "prtt_rate": "0.00",
                    "mod_yn": "N",
                    "prdy_vrss_sign": "2",
                    "prdy_vrss": "500",
                    "revl_issu_reas": "",
                },
                {
                    "stck_bsop_date": "20240103",
                    "stck_oprc": "70500",
                    "stck_hgpr": "71200",
                    "stck_lwpr": "69500",
                    "stck_clpr": "70000",
                    "acml_vol": "1200000",
                    "acml_tr_pbmn": "84000000000",
                    "flng_cls_code": "00",
                    "prtt_rate": "0.00",
                    "mod_yn": "N",
                    "prdy_vrss_sign": "5",
                    "prdy_vrss": "-500",
                    "revl_issu_reas": "",
                },
            ],
        }
    }

    db = Database(":memory:")
    client = FakeKISClient(responses)
    service = StockPriceService(db=db, client=client)

    result = service.get_periodic_prices(
        stock_code="005930",
        start_date="20240101",
        end_date="20240105",
        period="D",
        use_cache=True,
    )

    assert result["source"] == "kis"
    assert result["count"] == 2
    assert client.calls == ["005930"]

    cached = service.get_periodic_prices(
        stock_code="005930",
        start_date="20240101",
        end_date="20240105",
        period="D",
        use_cache=True,
    )

    assert cached["source"] == "db"
    assert cached["count"] == 2
    assert client.calls == ["005930"]


def test_periodic_prices_sk_hynix():
    responses = {
        "000660": {
            "rt_cd": "0",
            "output2": [
                {
                    "stck_bsop_date": "20240102",
                    "stck_oprc": "112000",
                    "stck_hgpr": "113000",
                    "stck_lwpr": "111000",
                    "stck_clpr": "112500",
                    "acml_vol": "800000",
                    "acml_tr_pbmn": "90000000000",
                    "flng_cls_code": "00",
                    "prtt_rate": "0.00",
                    "mod_yn": "N",
                    "prdy_vrss_sign": "2",
                    "prdy_vrss": "1000",
                    "revl_issu_reas": "",
                }
            ],
        }
    }

    db = Database(":memory:")
    client = FakeKISClient(responses)
    service = StockPriceService(db=db, client=client)

    result = service.get_periodic_prices(
        stock_code="000660",
        start_date="20240101",
        end_date="20240105",
        period="D",
        use_cache=False,
    )

    assert result["source"] == "kis"
    assert result["count"] == 1
    assert result["prices"][0]["stck_clpr"] == 112500
