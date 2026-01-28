"""
한국투자증권 API 클라이언트

한국투자증권 Open API 연동을 위한 전용 클라이언트입니다.
"""

from typing import Any

from external.auth import TokenManager
from external.client import BaseAPIClient
from core.config import KISConfig


class KISClient(BaseAPIClient):
    """
    한국투자증권 API 클라이언트

    토큰 자동 관리, 공통 헤더 설정 등을 제공합니다.
    """

    def __init__(self, config: KISConfig):
        """
        Args:
            config: 한국투자증권 API 설정
        """
        super().__init__(base_url=config.base_url)
        self.config = config
        self.token_manager = TokenManager(
            app_key=config.app_key,
            app_secret=config.app_secret,
            base_url=config.base_url,
        )

    async def _get_auth_headers(self, tr_id: str | None = None) -> dict[str, str]:
        """
        인증 헤더 생성

        Args:
            tr_id: 거래ID (API별로 다름)

        Returns:
            dict: 인증 관련 헤더
        """
        token = await self.token_manager.get_token()

        headers = {
            "authorization": f"Bearer {token}",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
        }

        if tr_id:
            headers["tr_id"] = tr_id

        return headers

    async def get(
        self,
        endpoint: str,
        tr_id: str | None = None,
        params: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        인증된 GET 요청

        Args:
            endpoint: API 엔드포인트
            tr_id: 거래ID
            params: 쿼리 파라미터
            extra_headers: 추가 헤더

        Returns:
            dict: JSON 응답
        """
        headers = await self._get_auth_headers(tr_id)
        if extra_headers:
            headers.update(extra_headers)

        return await super().get(endpoint, headers=headers, params=params)

    async def get_current_price(
        self,
        stock_code: str,
        market: str = "J",
        custtype: str = "P",
    ) -> dict[str, Any]:
        """국내주식 현재가 조회."""
        params = {
            "fid_cond_mrkt_div_code": market,
            "fid_input_iscd": stock_code,
        }
        extra_headers = {
            "content-type": "application/json; charset=utf-8",
            "custtype": custtype,
        }
        return await self.get(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params=params,
            extra_headers=extra_headers,
        )

    async def get_nxt_current_price(
        self,
        stock_code: str,
        custtype: str = "P",
    ) -> dict[str, Any]:
        """NXT 거래소 현재가 조회."""
        return await self.get_current_price(
            stock_code=stock_code,
            market="NX",
            custtype=custtype,
        )

    async def get_periodic_prices(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        period: str = "D",
        adj_price: bool = True,
        market: str = "J",
        custtype: str = "P",
    ) -> dict[str, Any]:
        """국내주식 기간별 시세 조회 (일/주/월/년)."""
        params = {
            "fid_cond_mrkt_div_code": market,
            "fid_input_iscd": stock_code,
            "fid_input_date_1": start_date,
            "fid_input_date_2": end_date,
            "fid_period_div_code": period,
            "fid_org_adj_prc": "0" if adj_price else "1",
        }
        extra_headers = {
            "content-type": "application/json; charset=utf-8",
            "custtype": custtype,
        }
        return await self.get(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            tr_id="FHKST03010100",
            params=params,
            extra_headers=extra_headers,
        )

    async def get_overseas_price(
        self,
        exchange: str,
        symbol: str,
        custtype: str = "P",
    ) -> dict[str, Any]:
        """해외주식 현재가상세 조회.

        Args:
            exchange: 거래소 코드 (NAS: 나스닥, NYS: 뉴욕)
            symbol: 종목코드 (예: TSLA, AAPL)
            custtype: 고객 타입 (P: 개인, B: 법인)

        Returns:
            dict: 해외주식 현재가 상세 정보
        """
        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": symbol,
        }
        extra_headers = {
            "content-type": "application/json; charset=utf-8",
            "custtype": custtype,
        }
        return await self.get(
            endpoint="/uapi/overseas-price/v1/quotations/price-detail",
            tr_id="HHDFS76200200",
            params=params,
            extra_headers=extra_headers,
        )

    async def get_overseas_periodic_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "D",
        market_code: str = "N",
        custtype: str = "P",
    ) -> dict[str, Any]:
        """해외주식 종목/지수/환율 기간별 시세 조회.

        Args:
            symbol: 종목/지수 코드 (예: .DJI, .IXIC, AAPL)
            start_date: 조회 시작일 (YYYYMMDD)
            end_date: 조회 종료일 (YYYYMMDD)
            period: 기간 구분 (D: 일, W: 주, M: 월, Y: 년)
            market_code: 시장 구분 (N: 해외지수, X: 환율, I: 국채, S: 금선물)
            custtype: 고객 타입 (P: 개인, B: 법인)

        Returns:
            dict: 기간별 시세 정보
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": market_code,
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": period,
        }
        extra_headers = {
            "content-type": "application/json; charset=utf-8",
            "custtype": custtype,
        }
        return await self.get(
            endpoint="/uapi/overseas-price/v1/quotations/inquire-daily-chartprice",
            tr_id="FHKST03030100",
            params=params,
            extra_headers=extra_headers,
        )

    async def post(
        self,
        endpoint: str,
        tr_id: str | None = None,
        json_data: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        인증된 POST 요청

        Args:
            endpoint: API 엔드포인트
            tr_id: 거래ID
            json_data: JSON 요청 본문
            extra_headers: 추가 헤더

        Returns:
            dict: JSON 응답
        """
        headers = await self._get_auth_headers(tr_id)
        if extra_headers:
            headers.update(extra_headers)

        return await super().post(endpoint, headers=headers, json_data=json_data)

    def get_token_info(self):
        """현재 토큰 정보 반환"""
        return self.token_manager.get_token_info()

    async def refresh_token(self) -> str:
        """토큰 강제 갱신"""
        self.token_manager.invalidate()
        return await self.token_manager.get_token()
