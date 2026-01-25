"""SQLite 데이터베이스 연결 관리."""
import sqlite3
from pathlib import Path
from typing import Optional

from .models import Stock, StockListing, StockPricePeriodic


class Database:
    """SQLite 데이터베이스 연결 및 테이블 관리."""

    def __init__(self, db_path: str = "data/stocks.db"):
        """데이터베이스 초기화.

        Args:
            db_path: SQLite 파일 경로
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """데이터베이스 연결."""
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
        return self.conn

    def close(self):
        """연결 종료."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_tables(self):
        """테이블 생성."""
        conn = self.connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                standard_code TEXT,
                name TEXT NOT NULL,
                market TEXT NOT NULL,
                exchange TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stocks_exchange ON stocks(exchange)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                exchange TEXT NOT NULL,
                is_primary INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (stock_code, exchange),
                FOREIGN KEY (stock_code) REFERENCES stocks(code) ON DELETE CASCADE
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stock_listings_code "
            "ON stock_listings(stock_code)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stock_listings_exchange "
            "ON stock_listings(exchange)"
        )
        self._migrate_stock_listings(conn)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_price_periodic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                market TEXT NOT NULL,
                period TEXT NOT NULL,
                adj_price INTEGER NOT NULL,
                business_date TEXT NOT NULL,
                open_price INTEGER,
                high_price INTEGER,
                low_price INTEGER,
                close_price INTEGER,
                volume INTEGER,
                trade_amount INTEGER,
                flng_cls_code TEXT,
                prtt_rate REAL,
                mod_yn TEXT,
                prdy_vrss_sign TEXT,
                prdy_vrss INTEGER,
                revl_issu_reas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (stock_code, market, period, adj_price, business_date)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stock_price_periodic_code_date "
            "ON stock_price_periodic(stock_code, business_date)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stock_price_periodic_period "
            "ON stock_price_periodic(period)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kis_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_key TEXT NOT NULL,
                base_url TEXT NOT NULL,
                access_token TEXT NOT NULL,
                token_type TEXT,
                expires_in INTEGER,
                expired_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (app_key, base_url)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_kis_tokens_app_base "
            "ON kis_tokens(app_key, base_url)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_price_current (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                market TEXT NOT NULL,
                price_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (stock_code, market)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stock_price_current_code "
            "ON stock_price_current(stock_code)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watchlist_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                is_default INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (watchlist_id, name),
                FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watchlist_id INTEGER NOT NULL,
                folder_id INTEGER,
                stock_code TEXT NOT NULL,
                memo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE,
                FOREIGN KEY (folder_id) REFERENCES watchlist_folders(id) ON DELETE CASCADE
            )
        """)
        self._migrate_watchlist_items_nullable(conn)
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_items_folder_unique "
            "ON watchlist_items(folder_id, stock_code) WHERE folder_id IS NOT NULL"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_items_root_unique "
            "ON watchlist_items(watchlist_id, stock_code) WHERE folder_id IS NULL"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_watchlist_items_stock_code "
            "ON watchlist_items(stock_code)"
        )
        conn.commit()

    def _migrate_watchlist_items_nullable(self, conn: sqlite3.Connection) -> None:
        """folder_id가 NOT NULL로 생성된 기존 DB를 NULL 허용 스키마로 마이그레이션."""
        cursor = conn.execute("PRAGMA table_info(watchlist_items)")
        columns = cursor.fetchall()
        if not columns:
            return

        folder_column = next((col for col in columns if col["name"] == "folder_id"), None)
        if not folder_column or folder_column["notnull"] == 0:
            return

        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("""
            CREATE TABLE watchlist_items_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watchlist_id INTEGER NOT NULL,
                folder_id INTEGER,
                stock_code TEXT NOT NULL,
                memo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE,
                FOREIGN KEY (folder_id) REFERENCES watchlist_folders(id) ON DELETE CASCADE
            )
        """)
        conn.execute(
            """
            INSERT INTO watchlist_items_new (
                id, watchlist_id, folder_id, stock_code, memo, created_at, updated_at
            )
            SELECT id, watchlist_id, folder_id, stock_code, memo, created_at, updated_at
            FROM watchlist_items
            """
        )
        conn.execute("DROP TABLE watchlist_items")
        conn.execute("ALTER TABLE watchlist_items_new RENAME TO watchlist_items")
        conn.execute("PRAGMA foreign_keys = ON")

    def insert_stocks(self, stocks: list[Stock]) -> int:
        """종목 일괄 삽입 (중복 시 업데이트).

        Args:
            stocks: 종목 리스트

        Returns:
            삽입된 종목 수
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.executemany(
            """
            INSERT INTO stocks (code, standard_code, name, market, exchange)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                standard_code = excluded.standard_code,
                name = excluded.name,
                market = excluded.market,
                exchange = excluded.exchange
            """,
            [(s.code, s.standard_code, s.name, s.market, s.exchange) for s in stocks],
        )
        conn.commit()
        return len(stocks)

    def insert_stock_listings(self, listings: list[StockListing]) -> int:
        """거래소 상장 정보 일괄 삽입 (중복 시 업데이트)."""
        if not listings:
            return 0

        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO stock_listings (stock_code, exchange, is_primary)
            VALUES (?, ?, ?)
            ON CONFLICT(stock_code, exchange) DO UPDATE SET
                is_primary = excluded.is_primary,
                updated_at = CURRENT_TIMESTAMP
            """,
            [(l.stock_code, l.exchange, l.is_primary) for l in listings],
        )
        conn.commit()
        return len(listings)

    def insert_periodic_prices(self, prices: list[StockPricePeriodic]) -> int:
        """기간별 시세 데이터 일괄 삽입 (중복 시 업데이트)."""
        if not prices:
            return 0

        conn = self.connect()
        cursor = conn.cursor()

        cursor.executemany(
            """
            INSERT INTO stock_price_periodic (
                stock_code,
                market,
                period,
                adj_price,
                business_date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                trade_amount,
                flng_cls_code,
                prtt_rate,
                mod_yn,
                prdy_vrss_sign,
                prdy_vrss,
                revl_issu_reas
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(stock_code, market, period, adj_price, business_date) DO UPDATE SET
                open_price = excluded.open_price,
                high_price = excluded.high_price,
                low_price = excluded.low_price,
                close_price = excluded.close_price,
                volume = excluded.volume,
                trade_amount = excluded.trade_amount,
                flng_cls_code = excluded.flng_cls_code,
                prtt_rate = excluded.prtt_rate,
                mod_yn = excluded.mod_yn,
                prdy_vrss_sign = excluded.prdy_vrss_sign,
                prdy_vrss = excluded.prdy_vrss,
                revl_issu_reas = excluded.revl_issu_reas,
                updated_at = CURRENT_TIMESTAMP
            """,
            [
                (
                    p.stock_code,
                    p.market,
                    p.period,
                    p.adj_price,
                    p.business_date,
                    p.open_price,
                    p.high_price,
                    p.low_price,
                    p.close_price,
                    p.volume,
                    p.trade_amount,
                    p.flng_cls_code,
                    p.prtt_rate,
                    p.mod_yn,
                    p.prdy_vrss_sign,
                    p.prdy_vrss,
                    p.revl_issu_reas,
                )
                for p in prices
            ],
        )
        conn.commit()
        return len(prices)

    def get_periodic_prices(
        self,
        stock_code: str,
        market: str,
        period: str,
        adj_price: int,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """기간별 시세 데이터 조회."""
        conn = self.connect()
        cursor = conn.execute(
            """
            SELECT
                stock_code,
                market,
                period,
                adj_price,
                business_date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                trade_amount,
                flng_cls_code,
                prtt_rate,
                mod_yn,
                prdy_vrss_sign,
                prdy_vrss,
                revl_issu_reas
            FROM stock_price_periodic
            WHERE stock_code = ?
              AND market = ?
              AND period = ?
              AND adj_price = ?
              AND business_date BETWEEN ? AND ?
            ORDER BY business_date
            """,
            (stock_code, market, period, adj_price, start_date, end_date),
        )
        rows = cursor.fetchall()
        return [
            {
                "stock_code": row["stock_code"],
                "market": row["market"],
                "period": row["period"],
                "adj_price": row["adj_price"],
                "business_date": row["business_date"],
                "open_price": row["open_price"],
                "high_price": row["high_price"],
                "low_price": row["low_price"],
                "close_price": row["close_price"],
                "volume": row["volume"],
                "trade_amount": row["trade_amount"],
                "flng_cls_code": row["flng_cls_code"],
                "prtt_rate": row["prtt_rate"],
                "mod_yn": row["mod_yn"],
                "prdy_vrss_sign": row["prdy_vrss_sign"],
                "prdy_vrss": row["prdy_vrss"],
                "revl_issu_reas": row["revl_issu_reas"],
            }
            for row in rows
        ]

    def upsert_kis_token(
        self,
        app_key: str,
        base_url: str,
        access_token: str,
        token_type: str | None,
        expires_in: int | None,
        expired_at: str | None,
    ) -> None:
        """KIS 토큰 저장/갱신."""
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO kis_tokens (
                app_key,
                base_url,
                access_token,
                token_type,
                expires_in,
                expired_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(app_key, base_url) DO UPDATE SET
                access_token = excluded.access_token,
                token_type = excluded.token_type,
                expires_in = excluded.expires_in,
                expired_at = excluded.expired_at,
                updated_at = CURRENT_TIMESTAMP
            """,
            (app_key, base_url, access_token, token_type, expires_in, expired_at),
        )
        conn.commit()

    def get_kis_token(self, app_key: str, base_url: str) -> dict | None:
        """KIS 저장 토큰 조회."""
        conn = self.connect()
        cursor = conn.execute(
            """
            SELECT access_token, token_type, expires_in, expired_at
            FROM kis_tokens
            WHERE app_key = ? AND base_url = ?
            LIMIT 1
            """,
            (app_key, base_url),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "access_token": row["access_token"],
            "token_type": row["token_type"],
            "expires_in": row["expires_in"],
            "expired_at": row["expired_at"],
        }

    def delete_kis_token(self, app_key: str, base_url: str) -> None:
        """저장된 KIS 토큰 삭제."""
        conn = self.connect()
        conn.execute(
            "DELETE FROM kis_tokens WHERE app_key = ? AND base_url = ?",
            (app_key, base_url),
        )
        conn.commit()

    def upsert_current_price(self, stock_code: str, market: str, price_json: str) -> None:
        """현재가 데이터 저장/갱신."""
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO stock_price_current (
                stock_code,
                market,
                price_json
            )
            VALUES (?, ?, ?)
            ON CONFLICT(stock_code, market) DO UPDATE SET
                price_json = excluded.price_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (stock_code, market, price_json),
        )
        conn.commit()

    def get_current_price(self, stock_code: str, market: str) -> dict | None:
        """저장된 현재가 조회."""
        conn = self.connect()
        cursor = conn.execute(
            """
            SELECT price_json, updated_at
            FROM stock_price_current
            WHERE stock_code = ? AND market = ?
            LIMIT 1
            """,
            (stock_code, market),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "price_json": row["price_json"],
            "updated_at": row["updated_at"],
        }

    def get_stock_count(self, market: Optional[str] = None, exchange: Optional[str] = None) -> int:
        """종목 수 조회.

        Args:
            market: 시장 필터 (KOSPI/KOSDAQ)
            exchange: 거래소 필터 (KRX/NXT)

        Returns:
            종목 수
        """
        conn = self.connect()
        params = []
        if exchange:
            query = """
                SELECT COUNT(DISTINCT s.code)
                FROM stocks s
                JOIN stock_listings l ON l.stock_code = s.code
                WHERE l.exchange = ?
            """
            params.append(exchange)
            if market:
                query += " AND s.market = ?"
                params.append(market)
        else:
            query = "SELECT COUNT(*) FROM stocks WHERE 1=1"
            if market:
                query += " AND market = ?"
                params.append(market)

        cursor = conn.execute(query, params)
        return cursor.fetchone()[0]

    def _migrate_stock_listings(self, conn: sqlite3.Connection) -> None:
        """stock_listings 테이블 초기 데이터 마이그레이션."""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stock_listings'"
        )
        if not cursor.fetchone():
            return

        count = conn.execute("SELECT COUNT(*) FROM stock_listings").fetchone()[0]
        if count:
            return

        conn.execute(
            """
            INSERT INTO stock_listings (stock_code, exchange, is_primary)
            SELECT code, exchange, 1
            FROM stocks
            WHERE exchange IS NOT NULL AND exchange != ''
            """
        )

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
