"""해외주식 현재가 조회 서비스 테스트."""

from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.oversea_stock_price_service import OverseaStockPriceService  # noqa: E402


class FakeKISClient:
    """KIS 클라이언트 테스트 더블."""

    def __init__(self, responses: dict[str, dict]):
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    async def get_overseas_price(
        self,
        exchange: str,
        symbol: str,
        custtype: str = "P",
    ) -> dict:
        self.calls.append((exchange, symbol))
        key = f"{exchange}:{symbol}"
        return self.responses.get(key, {"rt_cd": "1", "msg_cd": "NOT_FOUND", "msg1": "종목을 찾을 수 없습니다."})


@pytest.mark.asyncio
async def test_overseas_price_nasdaq():
    """나스닥 종목 조회 테스트."""
    responses = {
        "NAS:TSLA": {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "rsym": "DNASTSLA",
                "last": "245.0100",
                "base": "258.0800",
                "open": "257.2600",
                "high": "259.0794",
                "low": "242.0100",
                "tvol": "132541640",
                "tamt": "32907071789",
                "pvol": "108861698",
                "pamt": "28090405673",
                "perx": "69.51",
                "pbrx": "15.21",
                "epsx": "3.52",
                "bpsx": "16.11",
                "h52p": "313.8000",
                "h52d": "20220921",
                "l52p": "101.8100",
                "l52d": "20230106",
                "tomv": "777659289900",
                "shar": "3173990000",
                "curr": "USD",
                "t_xprc": "323658",
                "t_rate": "1321.00",
                "t_xdif": "17265",
                "t_xrat": "-5.06",
                "e_ordyn": "매매 가능",
                "e_hogau": "0.0100",
                "vnit": "1",
                "e_icod": "자동차",
            },
        }
    }

    client = FakeKISClient(responses)
    service = OverseaStockPriceService(client=client)

    result = await service.get_current_price(
        symbol="TSLA",
        exchange="NAS",
    )

    assert client.calls == [("NAS", "TSLA")]
    assert result["symbol"] == "TSLA"
    assert result["exchange"] == "NAS"
    assert result["price"]["last"] == "245.0100"
    assert result["price"]["base"] == "258.0800"
    assert result["indicators"]["per"] == "69.51"
    assert result["currency"] == "USD"


@pytest.mark.asyncio
async def test_overseas_price_nyse():
    """뉴욕 종목 조회 테스트."""
    responses = {
        "NYS:AAPL": {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "rsym": "DNYSAAPL",
                "last": "175.5000",
                "base": "173.2000",
                "open": "174.0000",
                "high": "176.2500",
                "low": "173.5000",
                "curr": "USD",
            },
        }
    }

    client = FakeKISClient(responses)
    service = OverseaStockPriceService(client=client)

    result = await service.get_current_price(
        symbol="aapl",  # 소문자 테스트
        exchange="nys",  # 소문자 테스트
    )

    assert client.calls == [("NYS", "AAPL")]
    assert result["symbol"] == "AAPL"
    assert result["exchange"] == "NYS"


@pytest.mark.asyncio
async def test_invalid_exchange():
    """지원하지 않는 거래소 테스트."""
    client = FakeKISClient({})
    service = OverseaStockPriceService(client=client)

    with pytest.raises(ValueError, match="지원하지 않는 거래소"):
        await service.get_current_price(
            symbol="0700",
            exchange="HKS",  # 지원하지 않는 거래소
        )


@pytest.mark.asyncio
async def test_change_calculation():
    """등락 계산 테스트."""
    responses = {
        "NAS:NVDA": {
            "rt_cd": "0",
            "output": {
                "last": "110.0000",
                "base": "100.0000",
            },
        }
    }

    client = FakeKISClient(responses)
    service = OverseaStockPriceService(client=client)

    result = await service.get_current_price(
        symbol="NVDA",
        exchange="NAS",
    )

    assert result["change"]["diff"] == "10.0"
    assert result["change"]["rate"] == "10.0"


class FakeKISClientPeriodic:
    """기간별 시세용 KIS 클라이언트 테스트 더블."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.calls: list = []

    async def get_overseas_periodic_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "D",
        market_code: str = "N",
    ) -> dict:
        self.calls.append({
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "period": period,
            "market_code": market_code,
        })
        return self.responses.get(symbol, {"rt_cd": "1", "msg_cd": "NOT_FOUND"})


@pytest.mark.asyncio
async def test_periodic_prices_index():
    """해외지수 기간별 시세 조회 테스트."""
    responses = {
        ".DJI": {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "output1": {
                "hts_kor_isnm": "다우존스 산업지수",
                "ovrs_nmix_prpr": "30775.43",
                "ovrs_nmix_prdy_clpr": "31029.31",
                "ovrs_nmix_prdy_vrss": "-253.88",
                "prdy_ctrt": "-0.82",
                "prdy_vrss_sign": "5",
            },
            "output2": [
                {
                    "stck_bsop_date": "20240128",
                    "ovrs_nmix_prpr": "30775.43",
                    "ovrs_nmix_oprc": "30790.00",
                    "ovrs_nmix_hgpr": "30979.85",
                    "ovrs_nmix_lwpr": "30431.87",
                    "acml_vol": "397268510",
                },
                {
                    "stck_bsop_date": "20240127",
                    "ovrs_nmix_prpr": "31029.31",
                    "ovrs_nmix_oprc": "31000.00",
                    "ovrs_nmix_hgpr": "31200.00",
                    "ovrs_nmix_lwpr": "30900.00",
                    "acml_vol": "350000000",
                },
            ],
        }
    }

    client = FakeKISClientPeriodic(responses)
    service = OverseaStockPriceService(client=client)

    result = await service.get_periodic_prices(
        symbol=".DJI",
        start_date="2024-01-01",
        end_date="2024-01-28",
        period="D",
        market_code="N",
    )

    assert len(client.calls) == 1
    assert client.calls[0]["symbol"] == ".DJI"
    assert client.calls[0]["start_date"] == "20240101"  # 날짜 하이픈 제거 확인
    assert result["symbol"] == ".DJI"
    assert result["name"] == "다우존스 산업지수"
    assert result["count"] == 2
    assert result["prices"][0]["date"] == "20240128"
    assert result["current"]["price"] == "30775.43"


@pytest.mark.asyncio
async def test_invalid_period():
    """지원하지 않는 기간 테스트."""
    client = FakeKISClientPeriodic({})
    service = OverseaStockPriceService(client=client)

    with pytest.raises(ValueError, match="지원하지 않는 기간"):
        await service.get_periodic_prices(
            symbol=".DJI",
            start_date="20240101",
            end_date="20240128",
            period="X",  # 잘못된 기간
        )


@pytest.mark.asyncio
async def test_invalid_market_code():
    """지원하지 않는 시장 코드 테스트."""
    client = FakeKISClientPeriodic({})
    service = OverseaStockPriceService(client=client)

    with pytest.raises(ValueError, match="지원하지 않는 시장 코드"):
        await service.get_periodic_prices(
            symbol=".DJI",
            start_date="20240101",
            end_date="20240128",
            market_code="Z",  # 잘못된 시장 코드
        )

