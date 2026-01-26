"""주식 현재가 조회 서비스."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from core.config import load_config
from db import Database
from external.client import APIError
from external.kis import KISClient


@dataclass(frozen=True)
class CurrentPriceQuery:
    """현재가 조회 조건."""

    stock_code: str
    market: str
    use_cache: bool
    max_age_sec: int | None


class StockCurrentPriceService:
    """현재가 조회 서비스."""

    VALID_MARKETS = {"J", "NX", "UN"}

    def __init__(
        self,
        db: Database | None = None,
        client: KISClient | None = None,
    ):
        self.db = db or Database()
        self.db.create_tables()
        self.client = client

    def get_current_price(
        self,
        stock_code: str,
        market: str = "J",
        use_cache: bool = False,
        max_age_sec: int | None = None,
    ) -> dict:
        query = self._build_query(
            stock_code=stock_code,
            market=market,
            use_cache=use_cache,
            max_age_sec=max_age_sec,
        )

        if query.use_cache:
            cached = self.db.get_current_price(query.stock_code, query.market)
            if cached and self._is_cache_valid(cached.get("updated_at"), query.max_age_sec):
                return self._build_response(
                    query,
                    price=self._parse_price_json(cached.get("price_json")),
                    source="db",
                    updated_at=cached.get("updated_at"),
                )

        response = self._fetch_from_kis(query)
        output = response.get("output", {}) if isinstance(response, dict) else {}

        self.db.upsert_current_price(
            stock_code=query.stock_code,
            market=query.market,
            price_json=json.dumps(output, ensure_ascii=True),
        )

        return self._build_response(
            query,
            price=output,
            source="kis",
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    def _build_query(
        self,
        stock_code: str,
        market: str,
        use_cache: bool,
        max_age_sec: int | None,
    ) -> CurrentPriceQuery:
        if not stock_code:
            raise ValueError("stock_code 값이 필요합니다.")

        market = market.upper()
        if market not in self.VALID_MARKETS:
            raise ValueError("market은 J/NX/UN 중 하나여야 합니다.")

        if max_age_sec is not None and max_age_sec < 0:
            raise ValueError("max_age_sec는 0 이상이어야 합니다.")

        return CurrentPriceQuery(
            stock_code=stock_code,
            market=market,
            use_cache=use_cache,
            max_age_sec=max_age_sec,
        )

    def _fetch_from_kis(self, query: CurrentPriceQuery) -> dict:
        if self.client is None:
            self.client = KISClient(load_config())

        try:
            result = self.client.get_current_price(
                stock_code=query.stock_code,
                market=query.market,
            )
        except APIError as exc:
            raise APIError("현재가 API 호출 실패", status_code=exc.status_code, response=exc.response) from exc

        if result.get("rt_cd") != "0":
            message = result.get("msg1", "현재가 API 응답 오류")
            raise APIError(message, response=result)

        return result

    def _build_response(
        self,
        query: CurrentPriceQuery,
        price: dict,
        source: str,
        updated_at: str | None = None,
    ) -> dict:
        response = {
            "code": query.stock_code,
            "market": query.market,
            "source": source,
            "price": price,
        }
        if updated_at:
            response["updated_at"] = updated_at
        return response

    @staticmethod
    def _parse_price_json(value: str | None) -> dict:
        if not value:
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    def _is_cache_valid(self, updated_at: str | None, max_age_sec: int | None) -> bool:
        if not updated_at:
            return False
        if max_age_sec is None:
            return True

        parsed = self._parse_datetime(updated_at)
        if parsed is None:
            return False

        return datetime.now() - parsed <= timedelta(seconds=max_age_sec)

    def get_combined_price(
        self,
        stock_code: str,
        use_cache: bool = False,
        max_age_sec: int | None = None,
    ) -> dict:
        """KRX와 NXT 시세를 모두 조회하여 통합 결과 반환.

        Args:
            stock_code: 종목코드
            use_cache: 캐시 사용 여부
            max_age_sec: 캐시 최대 유효 시간(초)

        Returns:
            dict: KRX/NXT 각각의 시세와 최적 가격 정보
        """
        krx_price = None
        nxt_price = None
        krx_error = None
        nxt_error = None

        try:
            krx_result = self.get_current_price(
                stock_code=stock_code,
                market="J",
                use_cache=use_cache,
                max_age_sec=max_age_sec,
            )
            krx_price = krx_result.get("price", {})
        except Exception as e:
            krx_error = str(e)

        try:
            nxt_result = self.get_current_price(
                stock_code=stock_code,
                market="NX",
                use_cache=use_cache,
                max_age_sec=max_age_sec,
            )
            nxt_price = nxt_result.get("price", {})
        except Exception as e:
            nxt_error = str(e)

        best_price = self._select_best_price(krx_price, nxt_price)

        return {
            "code": stock_code,
            "krx": {"price": krx_price, "error": krx_error},
            "nxt": {"price": nxt_price, "error": nxt_error},
            "best": best_price,
            "active_exchanges": self.get_active_exchanges(),
        }

    def _select_best_price(
        self,
        krx_price: dict | None,
        nxt_price: dict | None,
    ) -> dict:
        """KRX와 NXT 중 최적 가격 선택.

        최신 거래 데이터가 있는 거래소 우선,
        동일 조건이면 거래량이 많은 거래소 선택.
        """
        krx_current = self._safe_int(krx_price.get("stck_prpr") if krx_price else None)
        nxt_current = self._safe_int(nxt_price.get("stck_prpr") if nxt_price else None)

        if krx_current and not nxt_current:
            return {"exchange": "KRX", "price": krx_current, "source": krx_price}
        if nxt_current and not krx_current:
            return {"exchange": "NXT", "price": nxt_current, "source": nxt_price}
        if not krx_current and not nxt_current:
            return {"exchange": None, "price": None, "source": None}

        # 둘 다 있으면 거래량 기준 선택
        krx_vol = self._safe_int(krx_price.get("acml_vol") if krx_price else None) or 0
        nxt_vol = self._safe_int(nxt_price.get("acml_vol") if nxt_price else None) or 0

        if nxt_vol > krx_vol:
            return {"exchange": "NXT", "price": nxt_current, "source": nxt_price}
        return {"exchange": "KRX", "price": krx_current, "source": krx_price}

    @staticmethod
    def _safe_int(value: str | int | None) -> int | None:
        """문자열을 안전하게 정수로 변환."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def get_active_exchanges(self, current_time: datetime | None = None) -> list[str]:
        """현재 시간에 활성화된 거래소 목록 반환.

        장전(08:00-08:50): NXT만
        정규장(09:00-15:20): KRX + NXT
        KRX 장마감(15:20-15:30): KRX만
        장후(15:40-20:00): NXT만
        그 외: 빈 리스트
        """
        if current_time is None:
            current_time = datetime.now()

        hour = current_time.hour
        minute = current_time.minute
        time_val = hour * 60 + minute

        # 시간대 상수 (분 단위)
        NXT_PRE_START = 8 * 60  # 08:00
        NXT_PRE_END = 8 * 60 + 50  # 08:50
        REGULAR_START = 9 * 60  # 09:00
        NXT_REGULAR_END = 15 * 60 + 20  # 15:20
        KRX_REGULAR_END = 15 * 60 + 30  # 15:30
        NXT_POST_START = 15 * 60 + 40  # 15:40
        NXT_POST_END = 20 * 60  # 20:00

        if NXT_PRE_START <= time_val < NXT_PRE_END:
            return ["NXT"]
        elif REGULAR_START <= time_val < NXT_REGULAR_END:
            return ["KRX", "NXT"]
        elif NXT_REGULAR_END <= time_val < KRX_REGULAR_END:
            return ["KRX"]
        elif NXT_POST_START <= time_val <= NXT_POST_END:
            return ["NXT"]
        else:
            return []

