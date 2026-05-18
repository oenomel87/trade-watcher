from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WatchItem:
    symbol: str
    name: str
    market: str
    exchange: str | None = None
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class CatalogEntry:
    symbol: str
    name: str
    market: str
    exchange: str | None = None
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    name: str
    market: str
    best_price: str | None
    krx_price: str | None
    nxt_price: str | None
    change_rate: str | None
    error: str | None = None
