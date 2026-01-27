"""Watch list 서비스."""

from __future__ import annotations

import asyncio
import sqlite3

from db import Database
from app.services.stock_current_price_service import StockCurrentPriceService


class WatchListService:
    """Watch list + 폴더 + 종목 관리 서비스."""

    DEFAULT_FOLDER_NAME = "기본"

    def __init__(self, db: Database | None = None):
        self.db = db or Database()
        self.db.create_tables()

    def create_watchlist(self, name: str, description: str | None = None) -> dict:
        if not name:
            raise ValueError("name 값이 필요합니다.")

        conn = self.db.connect()
        try:
            cursor = conn.execute(
                "INSERT INTO watchlists (name, description) VALUES (?, ?)",
                (name, description),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("이미 존재하는 watch list 이름입니다.") from exc

        watchlist_id = cursor.lastrowid
        default_folder = self._create_default_folder(watchlist_id)

        conn.commit()
        return {
            "id": watchlist_id,
            "name": name,
            "description": description,
            "default_folder": default_folder,
        }

    def list_watchlists(self) -> list[dict]:
        conn = self.db.connect()
        cursor = conn.execute(
            "SELECT id, name, description, created_at, updated_at FROM watchlists ORDER BY id"
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def get_watchlist(self, watchlist_id: int) -> dict | None:
        conn = self.db.connect()
        cursor = conn.execute(
            "SELECT id, name, description, created_at, updated_at FROM watchlists WHERE id = ?",
            (watchlist_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def delete_watchlist(self, watchlist_id: int) -> None:
        conn = self.db.connect()
        conn.execute("DELETE FROM watchlists WHERE id = ?", (watchlist_id,))
        conn.commit()

    def create_folder(
        self,
        watchlist_id: int,
        name: str,
        description: str | None = None,
    ) -> dict:
        if not name:
            raise ValueError("name 값이 필요합니다.")

        conn = self.db.connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO watchlist_folders (watchlist_id, name, description)
                VALUES (?, ?, ?)
                """,
                (watchlist_id, name, description),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("이미 존재하는 폴더 이름입니다.") from exc

        conn.commit()
        return {
            "id": cursor.lastrowid,
            "watchlist_id": watchlist_id,
            "name": name,
            "description": description,
        }

    def list_folders(self, watchlist_id: int) -> list[dict]:
        conn = self.db.connect()
        cursor = conn.execute(
            """
            SELECT id, watchlist_id, name, description, is_default, created_at, updated_at
            FROM watchlist_folders
            WHERE watchlist_id = ?
            ORDER BY id
            """,
            (watchlist_id,),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "watchlist_id": row["watchlist_id"],
                "name": row["name"],
                "description": row["description"],
                "is_default": bool(row["is_default"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def update_folder(
        self,
        watchlist_id: int,
        folder_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> dict | None:
        conn = self.db.connect()
        current = self._get_folder(watchlist_id, folder_id)
        if not current:
            return None

        new_name = name or current["name"]
        new_description = description if description is not None else current["description"]

        try:
            conn.execute(
                """
                UPDATE watchlist_folders
                SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND watchlist_id = ?
                """,
                (new_name, new_description, folder_id, watchlist_id),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("이미 존재하는 폴더 이름입니다.") from exc

        return {
            "id": folder_id,
            "watchlist_id": watchlist_id,
            "name": new_name,
            "description": new_description,
        }

    def delete_folder(self, watchlist_id: int, folder_id: int) -> None:
        folder = self._get_folder(watchlist_id, folder_id)
        if not folder:
            return
        if folder["is_default"]:
            raise ValueError("기본 폴더는 삭제할 수 없습니다.")

        conn = self.db.connect()
        conn.execute(
            "DELETE FROM watchlist_folders WHERE id = ? AND watchlist_id = ?",
            (folder_id, watchlist_id),
        )
        conn.commit()

    def add_item(
        self,
        watchlist_id: int,
        stock_code: str,
        folder_id: int | None = None,
        memo: str | None = None,
    ) -> dict:
        if not stock_code:
            raise ValueError("stock_code 값이 필요합니다.")

        if folder_id is not None:
            folder = self._get_folder(watchlist_id, folder_id)
            if not folder:
                raise ValueError("폴더를 찾을 수 없습니다.")

        conn = self.db.connect()
        if folder_id is None:
            try:
                conn.execute(
                    """
                    INSERT INTO watchlist_items (watchlist_id, folder_id, stock_code, memo)
                    VALUES (?, NULL, ?, ?)
                    """,
                    (watchlist_id, stock_code, memo),
                )
            except sqlite3.IntegrityError:
                conn.execute(
                    """
                    UPDATE watchlist_items
                    SET memo = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE watchlist_id = ? AND stock_code = ? AND folder_id IS NULL
                    """,
                    (memo, watchlist_id, stock_code),
                )
        else:
            try:
                conn.execute(
                    """
                    INSERT INTO watchlist_items (watchlist_id, folder_id, stock_code, memo)
                    VALUES (?, ?, ?, ?)
                    """,
                    (watchlist_id, folder_id, stock_code, memo),
                )
            except sqlite3.IntegrityError:
                conn.execute(
                    """
                    UPDATE watchlist_items
                    SET memo = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE watchlist_id = ? AND stock_code = ? AND folder_id = ?
                    """,
                    (memo, watchlist_id, stock_code, folder_id),
                )
        conn.commit()

        return {
            "watchlist_id": watchlist_id,
            "folder_id": folder_id,
            "stock_code": stock_code,
            "memo": memo,
        }

    def list_items(self, watchlist_id: int, folder_id: int | None = None) -> list[dict]:
        conn = self.db.connect()
        if folder_id is None:
            cursor = conn.execute(
                """
                SELECT id, watchlist_id, folder_id, stock_code, memo, created_at, updated_at
                FROM watchlist_items
                WHERE watchlist_id = ?
                ORDER BY id
                """,
                (watchlist_id,),
            )
        else:
            cursor = conn.execute(
                """
                SELECT id, watchlist_id, folder_id, stock_code, memo, created_at, updated_at
                FROM watchlist_items
                WHERE watchlist_id = ? AND folder_id = ?
                ORDER BY id
                """,
                (watchlist_id, folder_id),
            )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "watchlist_id": row["watchlist_id"],
                "folder_id": row["folder_id"],
                "stock_code": row["stock_code"],
                "memo": row["memo"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def delete_item(self, watchlist_id: int, item_id: int) -> None:
        conn = self.db.connect()
        conn.execute(
            "DELETE FROM watchlist_items WHERE id = ? AND watchlist_id = ?",
            (item_id, watchlist_id),
        )
        conn.commit()

    async def list_items_with_price(
        self,
        watchlist_id: int,
        folder_id: int | None = None,
        use_cache: bool = True,
        max_age_sec: int | None = None,
        refresh_missing: bool = False,
        market: str = "J",
        include_nxt: bool = False,
    ) -> list[dict]:
        """종목 목록과 현재가 조회 (비동기, 동시 조회).

        Args:
            watchlist_id: watch list ID
            folder_id: 폴더 ID (선택, None이면 전체)
            use_cache: 캐시 사용 여부
            max_age_sec: 캐시 최대 유효 시간(초)
            refresh_missing: 캐시 없을 때 API 호출 여부
            market: 시장 구분 (J/NX)
            include_nxt: NXT 시세 추가 포함 여부
        """
        items = self.list_items(watchlist_id, folder_id)
        price_service = StockCurrentPriceService(db=self.db)

        async def fetch_item_price(item: dict) -> dict:
            price_payload = {}
            source = None
            nxt_price_payload = {}
            nxt_source = None

            # 캐시 조회
            if use_cache:
                cached = self.db.get_current_price(item["stock_code"], market)
                if cached:
                    price_payload = price_service._parse_price_json(cached.get("price_json"))
                    if price_payload and price_service._is_cache_valid(
                        cached.get("updated_at"), max_age_sec
                    ):
                        source = "db"
                    else:
                        price_payload = {}

            # 캐시 없으면 API 호출
            if refresh_missing and not price_payload:
                try:
                    live = await price_service.get_current_price(
                        stock_code=item["stock_code"],
                        market=market,
                        use_cache=False,
                    )
                    price_payload = live.get("price", {}) if isinstance(live, dict) else {}
                    source = live.get("source") if isinstance(live, dict) else "kis"
                except Exception:
                    price_payload = {}
                    source = "error"

            # NXT 시세 추가 조회
            if include_nxt:
                if use_cache:
                    nxt_cached = self.db.get_current_price(item["stock_code"], "NX")
                    if nxt_cached:
                        nxt_price_payload = price_service._parse_price_json(
                            nxt_cached.get("price_json")
                        )
                        if nxt_price_payload and price_service._is_cache_valid(
                            nxt_cached.get("updated_at"), max_age_sec
                        ):
                            nxt_source = "db"
                        else:
                            nxt_price_payload = {}

                if refresh_missing and not nxt_price_payload:
                    try:
                        nxt_live = await price_service.get_current_price(
                            stock_code=item["stock_code"],
                            market="NX",
                            use_cache=False,
                        )
                        nxt_price_payload = (
                            nxt_live.get("price", {}) if isinstance(nxt_live, dict) else {}
                        )
                        nxt_source = nxt_live.get("source") if isinstance(nxt_live, dict) else "kis"
                    except Exception:
                        nxt_price_payload = {}
                        nxt_source = "error"

            result_item = {
                **item,
                "price_source": source,
                "current_price": price_payload.get("stck_prpr"),
                "volume": price_payload.get("acml_vol"),
                "change": price_payload.get("prdy_vrss"),
                "change_rate": price_payload.get("prdy_ctrt"),
            }

            if include_nxt:
                result_item["nxt_price_source"] = nxt_source
                result_item["nxt_current_price"] = nxt_price_payload.get("stck_prpr")
                result_item["nxt_volume"] = nxt_price_payload.get("acml_vol")
                result_item["nxt_change"] = nxt_price_payload.get("prdy_vrss")
                result_item["nxt_change_rate"] = nxt_price_payload.get("prdy_ctrt")

            return result_item

        # 모든 종목 동시 조회
        results = await asyncio.gather(*[fetch_item_price(item) for item in items])
        return list(results)

    def _create_default_folder(self, watchlist_id: int) -> dict:
        conn = self.db.connect()
        cursor = conn.execute(
            """
            INSERT INTO watchlist_folders (watchlist_id, name, description, is_default)
            VALUES (?, ?, ?, 1)
            """,
            (watchlist_id, self.DEFAULT_FOLDER_NAME, "기본 폴더"),
        )
        return {
            "id": cursor.lastrowid,
            "watchlist_id": watchlist_id,
            "name": self.DEFAULT_FOLDER_NAME,
            "description": "기본 폴더",
            "is_default": True,
        }

    def _ensure_default_folder(self, watchlist_id: int) -> int:
        conn = self.db.connect()
        cursor = conn.execute(
            """
            SELECT id
            FROM watchlist_folders
            WHERE watchlist_id = ? AND is_default = 1
            LIMIT 1
            """,
            (watchlist_id,),
        )
        row = cursor.fetchone()
        if row:
            return row["id"]

        default_folder = self._create_default_folder(watchlist_id)
        conn.commit()
        return default_folder["id"]

    def _get_folder(self, watchlist_id: int, folder_id: int) -> dict | None:
        conn = self.db.connect()
        cursor = conn.execute(
            """
            SELECT id, watchlist_id, name, description, is_default
            FROM watchlist_folders
            WHERE watchlist_id = ? AND id = ?
            """,
            (watchlist_id, folder_id),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "watchlist_id": row["watchlist_id"],
            "name": row["name"],
            "description": row["description"],
            "is_default": bool(row["is_default"]),
        }
