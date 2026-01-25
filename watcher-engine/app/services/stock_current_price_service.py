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
