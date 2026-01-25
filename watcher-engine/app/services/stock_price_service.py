"""주식 기간별 시세 서비스."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.config import load_config
from db import Database, StockPricePeriodic
from external.client import APIError
from external.kis import KISClient


@dataclass(frozen=True)
class PeriodicPriceQuery:
    """기간별 시세 조회 조건."""

    stock_code: str
    start_date: str
    end_date: str
    period: str
    market: str
    adj_price: bool


class StockPriceService:
    """기간별 시세 조회 서비스."""

    VALID_PERIODS = {"D", "W", "M", "Y"}
    VALID_MARKETS = {"J", "NX", "UN"}

    def __init__(
        self,
        db: Database | None = None,
        client: KISClient | None = None,
    ):
        self.db = db or Database()
        self.db.create_tables()
        self.client = client

    def get_periodic_prices(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        period: str = "D",
        market: str = "J",
        adj_price: bool = True,
        use_cache: bool = True,
    ) -> dict:
        query = self._build_query(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            period=period,
            market=market,
            adj_price=adj_price,
        )

        if use_cache:
            cached = self.db.get_periodic_prices(
                stock_code=query.stock_code,
                market=query.market,
                period=query.period,
                adj_price=0 if query.adj_price else 1,
                start_date=query.start_date,
                end_date=query.end_date,
            )
            if cached:
                return self._build_response(
                    query,
                    [self._db_row_to_response(row) for row in cached],
                    source="db",
                )

        response = self._fetch_from_kis(query)
        output2 = response.get("output2", []) if isinstance(response, dict) else []

        prices = [self._map_output_to_model(query, item) for item in output2]
        prices.sort(key=lambda item: item.business_date)
        self.db.insert_periodic_prices(prices)

        return self._build_response(
            query, [self._model_to_response(p) for p in prices], source="kis"
        )

    def _build_query(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        period: str,
        market: str,
        adj_price: bool,
    ) -> PeriodicPriceQuery:
        if not stock_code:
            raise ValueError("stock_code 값이 필요합니다.")

        period = period.upper()
        if period not in self.VALID_PERIODS:
            raise ValueError("period는 D/W/M/Y 중 하나여야 합니다.")

        market = market.upper()
        if market not in self.VALID_MARKETS:
            raise ValueError("market은 J/NX/UN 중 하나여야 합니다.")

        normalized_start = self._normalize_date(start_date)
        normalized_end = self._normalize_date(end_date)

        if normalized_start > normalized_end:
            raise ValueError("start_date는 end_date 이전이어야 합니다.")

        return PeriodicPriceQuery(
            stock_code=stock_code,
            start_date=normalized_start,
            end_date=normalized_end,
            period=period,
            market=market,
            adj_price=adj_price,
        )

    def _normalize_date(self, value: str) -> str:
        """YYYYMMDD 또는 YYYY-MM-DD를 YYYYMMDD로 정규화."""
        if not value:
            raise ValueError("날짜 값이 필요합니다.")

        if value.isdigit() and len(value) == 8:
            return value

        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("날짜는 YYYYMMDD 또는 YYYY-MM-DD 형식이어야 합니다.") from exc

        return parsed.strftime("%Y%m%d")

    def _fetch_from_kis(self, query: PeriodicPriceQuery) -> dict:
        if self.client is None:
            self.client = KISClient(load_config())
        try:
            result = self.client.get_periodic_prices(
                stock_code=query.stock_code,
                start_date=query.start_date,
                end_date=query.end_date,
                period=query.period,
                adj_price=query.adj_price,
                market=query.market,
            )
        except APIError as exc:
            raise APIError("기간별 시세 API 호출 실패", status_code=exc.status_code, response=exc.response) from exc

        if result.get("rt_cd") != "0":
            message = result.get("msg1", "기간별 시세 API 응답 오류")
            raise APIError(message, response=result)

        return result

    def _map_output_to_model(
        self, query: PeriodicPriceQuery, item: dict
    ) -> StockPricePeriodic:
        return StockPricePeriodic(
            stock_code=query.stock_code,
            market=query.market,
            period=query.period,
            adj_price=0 if query.adj_price else 1,
            business_date=item.get("stck_bsop_date", ""),
            open_price=self._to_int(item.get("stck_oprc")),
            high_price=self._to_int(item.get("stck_hgpr")),
            low_price=self._to_int(item.get("stck_lwpr")),
            close_price=self._to_int(item.get("stck_clpr")),
            volume=self._to_int(item.get("acml_vol")),
            trade_amount=self._to_int(item.get("acml_tr_pbmn")),
            flng_cls_code=item.get("flng_cls_code"),
            prtt_rate=self._to_float(item.get("prtt_rate")),
            mod_yn=item.get("mod_yn"),
            prdy_vrss_sign=item.get("prdy_vrss_sign"),
            prdy_vrss=self._to_int(item.get("prdy_vrss")),
            revl_issu_reas=item.get("revl_issu_reas"),
        )

    def _model_to_response(self, price: StockPricePeriodic) -> dict:
        return {
            "stck_bsop_date": price.business_date,
            "stck_oprc": price.open_price,
            "stck_hgpr": price.high_price,
            "stck_lwpr": price.low_price,
            "stck_clpr": price.close_price,
            "acml_vol": price.volume,
            "acml_tr_pbmn": price.trade_amount,
            "flng_cls_code": price.flng_cls_code,
            "prtt_rate": price.prtt_rate,
            "mod_yn": price.mod_yn,
            "prdy_vrss_sign": price.prdy_vrss_sign,
            "prdy_vrss": price.prdy_vrss,
            "revl_issu_reas": price.revl_issu_reas,
        }

    def _db_row_to_response(self, row: dict) -> dict:
        return {
            "stck_bsop_date": row.get("business_date"),
            "stck_oprc": row.get("open_price"),
            "stck_hgpr": row.get("high_price"),
            "stck_lwpr": row.get("low_price"),
            "stck_clpr": row.get("close_price"),
            "acml_vol": row.get("volume"),
            "acml_tr_pbmn": row.get("trade_amount"),
            "flng_cls_code": row.get("flng_cls_code"),
            "prtt_rate": row.get("prtt_rate"),
            "mod_yn": row.get("mod_yn"),
            "prdy_vrss_sign": row.get("prdy_vrss_sign"),
            "prdy_vrss": row.get("prdy_vrss"),
            "revl_issu_reas": row.get("revl_issu_reas"),
        }

    def _build_response(self, query: PeriodicPriceQuery, prices: list[dict], source: str) -> dict:
        return {
            "code": query.stock_code,
            "market": query.market,
            "period": query.period,
            "start_date": query.start_date,
            "end_date": query.end_date,
            "adj_price": query.adj_price,
            "source": source,
            "count": len(prices),
            "prices": prices,
        }

    @staticmethod
    def _to_int(value: str | None) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_float(value: str | None) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
