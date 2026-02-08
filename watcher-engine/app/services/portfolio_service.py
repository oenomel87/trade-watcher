"""포트폴리오 서비스 (FIFO 손익 계산)."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime

from db import Database, HoldingLot, Trade


class PortfolioService:
    """포트폴리오 관리 서비스."""

    def __init__(self, db: Database | None = None):
        self.db = db or Database()
        self.db.create_tables()

    def buy_stock(
        self,
        stock_code: str,
        quantity: int,
        price: float,
        buy_date: str,
        memo: str | None = None,
    ) -> dict:
        """주식 매수 - 새로운 Lot 생성."""
        code = self._validate_stock_code(stock_code)
        qty = self._validate_quantity(quantity)
        buy_price = self._validate_price(price)
        self._validate_date(buy_date)

        lot = HoldingLot(
            stock_code=code,
            quantity=qty,
            buy_price=buy_price,
            buy_date=buy_date,
            remaining_qty=qty,
            is_closed=False,
            memo=memo,
        )
        lot_id = self.db.insert_holding_lot(lot)

        return {
            "id": lot_id,
            "stock_code": code,
            "quantity": qty,
            "buy_price": buy_price,
            "buy_date": buy_date,
            "remaining_qty": qty,
            "is_closed": False,
            "memo": memo,
        }

    def sell_stock(
        self,
        stock_code: str,
        quantity: int,
        price: float,
        sell_date: str,
        memo: str | None = None,
    ) -> dict:
        """주식 매도 - FIFO로 Lot 매칭하고 실현 손익 계산."""
        code = self._validate_stock_code(stock_code)
        sell_qty = self._validate_quantity(quantity)
        sell_price = self._validate_price(price)
        self._validate_date(sell_date)

        open_lots = self.db.get_open_lots(code)
        if not open_lots:
            raise ValueError("매도 가능한 보유 Lot이 없습니다.")

        available_qty = sum(lot.remaining_qty for lot in open_lots)
        if sell_qty > available_qty:
            raise ValueError(
                f"보유 수량이 부족합니다. 요청: {sell_qty}, 보유: {available_qty}"
            )

        remaining_to_sell = sell_qty
        realized_pnl = 0.0
        matched_lots: list[dict] = []
        matched_lots_detail: list[dict] = []
        lot_updates: list[tuple[int, int, bool]] = []

        for lot in open_lots:
            if remaining_to_sell == 0:
                break

            matched_qty = min(lot.remaining_qty, remaining_to_sell)
            if matched_qty <= 0:
                continue

            lot_realized_pnl = (sell_price - lot.buy_price) * matched_qty
            new_remaining_qty = lot.remaining_qty - matched_qty
            is_closed = new_remaining_qty == 0

            realized_pnl += lot_realized_pnl
            remaining_to_sell -= matched_qty

            matched_lots.append({"lot_id": lot.id, "quantity": matched_qty})
            matched_lots_detail.append(
                {
                    "lot_id": lot.id,
                    "buy_date": lot.buy_date,
                    "buy_price": lot.buy_price,
                    "sell_price": sell_price,
                    "matched_quantity": matched_qty,
                    "realized_pnl": lot_realized_pnl,
                }
            )
            lot_updates.append((int(lot.id), new_remaining_qty, is_closed))

        if remaining_to_sell != 0:
            raise RuntimeError("FIFO 매칭 계산에 실패했습니다.")

        conn = self.db.connect()
        try:
            conn.execute("BEGIN")

            for lot_id, new_remaining_qty, is_closed in lot_updates:
                conn.execute(
                    """
                    UPDATE holding_lots
                    SET remaining_qty = ?, is_closed = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (new_remaining_qty, 1 if is_closed else 0, lot_id),
                )

            cursor = conn.execute(
                """
                INSERT INTO trades (
                    stock_code,
                    trade_type,
                    quantity,
                    price,
                    trade_date,
                    realized_pnl,
                    matched_lots,
                    memo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    code,
                    "SELL",
                    sell_qty,
                    sell_price,
                    sell_date,
                    realized_pnl,
                    json.dumps(matched_lots),
                    memo,
                ),
            )

            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return {
            "trade_id": int(cursor.lastrowid),
            "realized_pnl": realized_pnl,
            "matched_lots_detail": matched_lots_detail,
        }

    def get_holdings(self) -> list[dict]:
        """현재 보유 중인 종목 목록 조회."""
        conn = self.db.connect()
        cursor = conn.execute(
            """
            SELECT
                id,
                stock_code,
                quantity,
                buy_price,
                buy_date,
                remaining_qty,
                is_closed,
                memo,
                created_at,
                updated_at
            FROM holding_lots
            WHERE is_closed = 0
            ORDER BY stock_code ASC, buy_date ASC, id ASC
            """
        )
        rows = cursor.fetchall()

        grouped: dict[str, dict] = defaultdict(
            lambda: {
                "stock_code": "",
                "total_quantity": 0,
                "total_cost": 0.0,
                "lots_count": 0,
            }
        )

        for row in rows:
            stock_code = row["stock_code"]
            remaining_qty = int(row["remaining_qty"])
            buy_price = float(row["buy_price"])

            item = grouped[stock_code]
            item["stock_code"] = stock_code
            item["total_quantity"] += remaining_qty
            item["total_cost"] += remaining_qty * buy_price
            item["lots_count"] += 1

        holdings: list[dict] = []
        for stock_code in sorted(grouped.keys()):
            item = grouped[stock_code]
            total_quantity = item["total_quantity"]
            avg_buy_price = (
                item["total_cost"] / total_quantity if total_quantity > 0 else 0.0
            )
            holdings.append(
                {
                    "stock_code": stock_code,
                    "total_quantity": total_quantity,
                    "avg_buy_price": avg_buy_price,
                    "lots_count": item["lots_count"],
                }
            )

        return holdings

    def get_pnl_summary(self) -> dict:
        """포트폴리오 손익 요약 조회."""
        trades = self.db.get_trades(trade_type="SELL")
        realized_pnl = sum((trade.realized_pnl or 0.0) for trade in trades)

        # 현재가 연동 전까지 미실현 손익은 0으로 고정한다.
        _ = self.get_holdings()
        unrealized_pnl = 0.0

        return {
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": realized_pnl + unrealized_pnl,
        }

    def get_trades(
        self,
        stock_code: str | None = None,
        trade_type: str | None = None,
    ) -> list[Trade]:
        """거래 내역 조회."""
        code = self._validate_stock_code(stock_code) if stock_code is not None else None

        normalized_trade_type = trade_type.upper() if trade_type is not None else None
        if normalized_trade_type is not None and normalized_trade_type not in {"BUY", "SELL"}:
            raise ValueError("trade_type은 BUY 또는 SELL 이어야 합니다.")

        return self.db.get_trades(stock_code=code, trade_type=normalized_trade_type)

    def _validate_stock_code(self, stock_code: str) -> str:
        if stock_code is None:
            raise ValueError("stock_code 값이 필요합니다.")

        code = stock_code.strip().upper()
        if not code:
            raise ValueError("stock_code 값이 필요합니다.")
        return code

    def _validate_quantity(self, quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("quantity는 1 이상이어야 합니다.")
        return quantity

    def _validate_price(self, price: float) -> float:
        if price <= 0:
            raise ValueError("price는 0보다 커야 합니다.")
        return price

    def _validate_date(self, date_str: str) -> None:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except (TypeError, ValueError) as exc:
            raise ValueError("날짜 형식은 YYYY-MM-DD 이어야 합니다.") from exc
