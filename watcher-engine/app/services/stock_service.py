"""종목 관련 비즈니스 로직"""

from db import Database, Stock, StockListing
from loaders import StockParser


class StockService:
    """종목 서비스"""

    def __init__(self, db: Database | None = None):
        self.db = db or Database()

    def load_stocks_from_files(self) -> dict:
        """파일에서 종목 데이터 로드 및 저장"""
        parser = StockParser()
        stocks = parser.parse_all()

        base_by_code: dict[str, Stock] = {}
        exchanges_by_code: dict[str, set[str]] = {}

        for stock in stocks:
            exchanges_by_code.setdefault(stock.code, set()).add(stock.exchange)
            if stock.code not in base_by_code:
                base_by_code[stock.code] = Stock(
                    code=stock.code,
                    standard_code=stock.standard_code,
                    name=stock.name,
                    market=stock.market,
                    exchange=stock.exchange,
                )
            else:
                current = base_by_code[stock.code]
                if not current.standard_code and stock.standard_code:
                    current.standard_code = stock.standard_code
                if not current.name and stock.name:
                    current.name = stock.name

        listings: list[StockListing] = []
        for code, exchanges in exchanges_by_code.items():
            primary = "KRX" if "KRX" in exchanges else sorted(exchanges)[0]
            base_by_code[code].exchange = primary
            for exchange in sorted(exchanges):
                listings.append(
                    StockListing(
                        stock_code=code,
                        exchange=exchange,
                        is_primary=1 if exchange == primary else 0,
                    )
                )

        with Database() as db:
            db.create_tables()
            count = db.insert_stocks(list(base_by_code.values()))
            db.insert_stock_listings(listings)

            result = {
                "total_parsed": len(stocks),
                "total_saved": count,
                "by_market": {},
            }

            market_exchanges = {
                "KOSPI": ["KRX", "NXT"],
                "KOSDAQ": ["KRX", "NXT"],
                "US": ["US"],
            }
            for market, exchanges in market_exchanges.items():
                for exchange in exchanges:
                    cnt = db.get_stock_count(market=market, exchange=exchange)
                    result["by_market"][f"{market}_{exchange}"] = cnt

            result["total_unique"] = db.get_stock_count()

        return result

    def get_stocks(
        self,
        market: str | None = None,
        exchange: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """종목 목록 조회"""
        conn = self.db.connect()
        if exchange:
            query = (
                "SELECT s.code, s.standard_code, s.name, s.market, l.exchange AS exchange "
                "FROM stocks s "
                "JOIN stock_listings l ON l.stock_code = s.code "
                "WHERE l.exchange = ?"
            )
            params = [exchange.upper()]
        else:
            query = (
                "SELECT s.code, s.standard_code, s.name, s.market, s.exchange "
                "FROM stocks s WHERE 1=1"
            )
            params = []
        if market:
            query += " AND s.market = ?"
            params.append(market.upper())

        query += " ORDER BY s.code LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        return [
            {
                "code": row["code"],
                "standard_code": row["standard_code"],
                "name": row["name"],
                "market": row["market"],
                "exchange": row["exchange"],
            }
            for row in rows
        ]

    def get_stock_by_code(self, code: str) -> dict | None:
        """종목 코드로 조회"""
        conn = self.db.connect()
        cursor = conn.execute(
            "SELECT code, standard_code, name, market, exchange FROM stocks WHERE code = ?",
            (code,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "code": row["code"],
            "standard_code": row["standard_code"],
            "name": row["name"],
            "market": row["market"],
            "exchange": row["exchange"],
        }

    def search_stocks(self, query: str, limit: int = 20) -> list[dict]:
        """종목 검색 (이름 또는 코드)"""
        conn = self.db.connect()
        search_term = f"%{query}%"

        cursor = conn.execute(
            """
            SELECT code, standard_code, name, market, exchange
            FROM stocks
            WHERE name LIKE ? OR code LIKE ?
            ORDER BY code
            LIMIT ?
            """,
            (search_term, search_term, limit),
        )
        rows = cursor.fetchall()

        return [
            {
                "code": row["code"],
                "standard_code": row["standard_code"],
                "name": row["name"],
                "market": row["market"],
                "exchange": row["exchange"],
            }
            for row in rows
        ]

    def get_stats(self) -> dict:
        """종목 통계"""
        with Database() as db:
            result = {
                "total": db.get_stock_count(),
                "by_market": {},
            }

            for market in ["KOSPI", "KOSDAQ", "US"]:
                result["by_market"][market] = db.get_stock_count(market=market)

            for exchange in ["KRX", "NXT", "US"]:
                result["by_market"][exchange] = db.get_stock_count(exchange=exchange)

        return result
