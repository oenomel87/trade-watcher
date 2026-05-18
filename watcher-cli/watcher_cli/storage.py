from __future__ import annotations

import json
from pathlib import Path

from watcher_cli.models import WatchItem


class JsonWatchlistStorage:
    def __init__(self, path: Path | None = None):
        self.path = path or Path.home() / ".config" / "trade-watcher" / "watchlist.json"

    def list_items(self) -> list[WatchItem]:
        payload = self._read_payload()
        return [
            WatchItem(
                symbol=item["symbol"],
                name=item["name"],
                market=item["market"],
                exchange=item.get("exchange"),
                aliases=tuple(item.get("aliases", [])),
            )
            for item in payload["items"]
        ]

    def add(self, item: WatchItem) -> bool:
        payload = self._read_payload()
        items = payload["items"]
        if any(existing["symbol"] == item.symbol for existing in items):
            return False

        items.append(
            {
                "symbol": item.symbol,
                "name": item.name,
                "market": item.market,
                "exchange": item.exchange,
                "aliases": list(item.aliases),
            }
        )
        self._write_payload(payload)
        return True

    def remove(self, query: str) -> WatchItem | None:
        payload = self._read_payload()
        normalized = query.strip().lower()

        for index, item in enumerate(payload["items"]):
            symbol = item["symbol"].lower()
            name = item["name"].lower()
            aliases = {alias.lower() for alias in item.get("aliases", [])}
            if normalized in {symbol, name, *aliases}:
                removed = payload["items"].pop(index)
                self._write_payload(payload)
                return WatchItem(
                    symbol=removed["symbol"],
                    name=removed["name"],
                    market=removed["market"],
                    exchange=removed.get("exchange"),
                    aliases=tuple(removed.get("aliases", [])),
                )
        return None

    def _read_payload(self) -> dict:
        if not self.path.exists():
            return {"version": 1, "items": []}

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"저장 파일을 읽을 수 없습니다: {self.path}") from exc

        if not isinstance(payload, dict):
            raise ValueError(f"저장 파일 형식이 올바르지 않습니다: {self.path}")

        payload.setdefault("version", 1)
        payload.setdefault("items", [])
        return payload

    def _write_payload(self, payload: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
