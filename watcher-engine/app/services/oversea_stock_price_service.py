"""해외주식 현재가 조회 서비스."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from external.kis import get_kis_client, KISClient
from external.client import APIError


@dataclass
class OverseaStockPriceQuery:
    """해외주식 현재가 조회 조건."""

    symbol: str
    exchange: str


class OverseaStockPriceService:
    """해외주식 현재가 조회 서비스."""

    VALID_EXCHANGES = {"NAS", "NYS"}

    def __init__(self, client: KISClient | None = None):
        """
        Args:
            client: KIS 클라이언트 (주입 가능)
        """
        self._client = client

    @property
    def client(self) -> KISClient:
        """KIS 클라이언트 반환."""
        if self._client is None:
            self._client = get_kis_client()
        return self._client

    async def get_current_price(
        self,
        symbol: str,
        exchange: str,
    ) -> dict[str, Any]:
        """해외주식 현재가 조회.

        Args:
            symbol: 종목코드 (예: TSLA, AAPL)
            exchange: 거래소 코드 (NAS: 나스닥, NYS: 뉴욕)

        Returns:
            dict: 현재가 정보

        Raises:
            ValueError: 지원하지 않는 거래소인 경우
            APIError: API 요청 실패 시
        """
        query = self._build_query(symbol, exchange)
        response = await self._fetch_from_kis(query)
        return self._build_response(query, response)

    def _build_query(
        self,
        symbol: str,
        exchange: str,
    ) -> OverseaStockPriceQuery:
        """조회 조건 객체 생성."""
        exchange_upper = exchange.upper()
        if exchange_upper not in self.VALID_EXCHANGES:
            raise ValueError(
                f"지원하지 않는 거래소입니다: {exchange}. "
                f"지원 거래소: {', '.join(sorted(self.VALID_EXCHANGES))}"
            )
        return OverseaStockPriceQuery(
            symbol=symbol.upper(),
            exchange=exchange_upper,
        )

    async def _fetch_from_kis(
        self,
        query: OverseaStockPriceQuery,
    ) -> dict[str, Any]:
        """KIS API에서 현재가 조회."""
        response = await self.client.get_overseas_price(
            exchange=query.exchange,
            symbol=query.symbol,
        )

        rt_cd = response.get("rt_cd")
        if rt_cd != "0":
            msg_cd = response.get("msg_cd", "")
            msg1 = response.get("msg1", "")
            raise APIError(
                message=f"API 오류: {msg_cd} - {msg1}",
                response=response,
            )

        return response

    def _build_response(
        self,
        query: OverseaStockPriceQuery,
        response: dict[str, Any],
    ) -> dict[str, Any]:
        """응답 포맷 생성."""
        output = response.get("output", {})

        return {
            "symbol": query.symbol,
            "exchange": query.exchange,
            "price": {
                "last": output.get("last"),
                "base": output.get("base"),
                "open": output.get("open"),
                "high": output.get("high"),
                "low": output.get("low"),
            },
            "change": {
                "diff": self._safe_diff(output.get("last"), output.get("base")),
                "rate": self._calc_rate(output.get("last"), output.get("base")),
            },
            "volume": {
                "current": output.get("tvol"),
                "amount": output.get("tamt"),
                "prev": output.get("pvol"),
                "prev_amount": output.get("pamt"),
            },
            "indicators": {
                "per": output.get("perx"),
                "pbr": output.get("pbrx"),
                "eps": output.get("epsx"),
                "bps": output.get("bpsx"),
            },
            "market_cap": output.get("tomv"),
            "shares": output.get("shar"),
            "week52": {
                "high": output.get("h52p"),
                "high_date": output.get("h52d"),
                "low": output.get("l52p"),
                "low_date": output.get("l52d"),
            },
            "currency": output.get("curr"),
            "exchange_rate": {
                "today": output.get("t_rate"),
                "prev": output.get("p_rate"),
            },
            "krw_converted": {
                "price": output.get("t_xprc"),
                "diff": output.get("t_xdif"),
                "rate": output.get("t_xrat"),
            },
            "trading": {
                "available": output.get("e_ordyn"),
                "tick_size": output.get("e_hogau"),
                "lot_size": output.get("vnit"),
            },
            "sector": output.get("e_icod"),
            "raw_output": output,
        }

    @staticmethod
    def _safe_diff(last: str | None, base: str | None) -> str | None:
        """가격 차이 계산."""
        try:
            if last and base:
                return str(round(float(last) - float(base), 4))
        except (ValueError, TypeError):
            pass
        return None

    @staticmethod
    def _calc_rate(last: str | None, base: str | None) -> str | None:
        """등락률 계산."""
        try:
            if last and base:
                base_f = float(base)
                if base_f != 0:
                    rate = ((float(last) - base_f) / base_f) * 100
                    return str(round(rate, 2))
        except (ValueError, TypeError, ZeroDivisionError):
            pass
        return None

    # 기간별 시세 조회
    VALID_MARKET_CODES = {"N", "X", "I", "S"}  # N:지수, X:환율, I:국채, S:금선물
    VALID_PERIODS = {"D", "W", "M", "Y"}

    async def get_periodic_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "D",
        market_code: str = "N",
    ) -> dict[str, Any]:
        """해외 종목/지수/환율 기간별 시세 조회.

        Args:
            symbol: 종목/지수 코드 (예: .DJI, .IXIC, AAPL)
            start_date: 조회 시작일 (YYYYMMDD)
            end_date: 조회 종료일 (YYYYMMDD)
            period: 기간 구분 (D: 일, W: 주, M: 월, Y: 년)
            market_code: 시장 구분 (N: 해외지수, X: 환율, I: 국채, S: 금선물)

        Returns:
            dict: 기간별 시세 정보

        Raises:
            ValueError: 잘못된 파라미터인 경우
            APIError: API 요청 실패 시
        """
        # 날짜 형식 정규화 (YYYY-MM-DD -> YYYYMMDD)
        start_date = start_date.replace("-", "")
        end_date = end_date.replace("-", "")

        # 파라미터 검증
        period_upper = period.upper()
        if period_upper not in self.VALID_PERIODS:
            raise ValueError(
                f"지원하지 않는 기간입니다: {period}. "
                f"지원 기간: {', '.join(sorted(self.VALID_PERIODS))}"
            )

        market_code_upper = market_code.upper()
        if market_code_upper not in self.VALID_MARKET_CODES:
            raise ValueError(
                f"지원하지 않는 시장 코드입니다: {market_code}. "
                f"지원 코드: N(지수), X(환율), I(국채), S(금선물)"
            )

        response = await self.client.get_overseas_periodic_prices(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            period=period_upper,
            market_code=market_code_upper,
        )

        rt_cd = response.get("rt_cd")
        if rt_cd != "0":
            msg_cd = response.get("msg_cd", "")
            msg1 = response.get("msg1", "")
            raise APIError(
                message=f"API 오류: {msg_cd} - {msg1}",
                response=response,
            )

        return self._build_periodic_response(symbol, response)

    def _build_periodic_response(
        self,
        symbol: str,
        response: dict[str, Any],
    ) -> dict[str, Any]:
        """기간별 시세 응답 포맷."""
        output1 = response.get("output1", {})
        output2 = response.get("output2", [])

        # 일자별 데이터 정리
        prices = []
        for item in output2:
            prices.append({
                "date": item.get("stck_bsop_date"),
                "close": item.get("ovrs_nmix_prpr"),
                "open": item.get("ovrs_nmix_oprc"),
                "high": item.get("ovrs_nmix_hgpr"),
                "low": item.get("ovrs_nmix_lwpr"),
                "volume": item.get("acml_vol"),
            })

        return {
            "symbol": symbol,
            "name": output1.get("hts_kor_isnm"),
            "current": {
                "price": output1.get("ovrs_nmix_prpr"),
                "prev_close": output1.get("ovrs_nmix_prdy_clpr"),
                "change": output1.get("ovrs_nmix_prdy_vrss"),
                "change_rate": output1.get("prdy_ctrt"),
                "change_sign": output1.get("prdy_vrss_sign"),
                "open": output1.get("ovrs_prod_oprc"),
                "high": output1.get("ovrs_prod_hgpr"),
                "low": output1.get("ovrs_prod_lwpr"),
                "volume": output1.get("acml_vol"),
                "prev_volume": output1.get("prdy_vol"),
            },
            "prices": prices,
            "count": len(prices),
        }
