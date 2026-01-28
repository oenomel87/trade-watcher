"""Pydantic models for engine responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Watchlist(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(extra="ignore")


class WatchlistFolder(BaseModel):
    id: int
    watchlist_id: int | None = None
    name: str
    description: str | None = None
    is_default: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(extra="ignore")


class WatchlistItem(BaseModel):
    id: int
    watchlist_id: int
    folder_id: int | None = None
    stock_code: str
    memo: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(extra="ignore")


class WatchlistItemSummary(BaseModel):
    id: int
    watchlist_id: int
    folder_id: int | None = None
    stock_code: str
    memo: str | None = None
    market: str | None = None
    exchange: str | None = None
    current_price: str | None = None
    volume: str | None = None
    change: str | None = None
    change_rate: str | None = None
    price_source: str | None = None
    # NXT fields
    nxt_current_price: str | None = None
    nxt_volume: str | None = None
    nxt_change: str | None = None
    nxt_change_rate: str | None = None
    nxt_price_source: str | None = None

    model_config = ConfigDict(extra="ignore")


class WatchlistDetail(Watchlist):
    folders: list[WatchlistFolder] = Field(default_factory=list)
    items: list[WatchlistItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class WatchlistCreateResponse(Watchlist):
    default_folder: WatchlistFolder | None = None

    model_config = ConfigDict(extra="ignore")


class WatchlistItemCreateResult(BaseModel):
    watchlist_id: int
    folder_id: int | None = None
    stock_code: str
    memo: str | None = None

    model_config = ConfigDict(extra="ignore")


class Stock(BaseModel):
    code: str
    standard_code: str | None = None
    name: str
    market: str | None = None
    exchange: str | None = None

    model_config = ConfigDict(extra="ignore")


class StockSearchResponse(BaseModel):
    stocks: list[Stock] = Field(default_factory=list)
    count: int = 0

    model_config = ConfigDict(extra="ignore")


class PeriodicPricePoint(BaseModel):
    stck_bsop_date: str
    stck_oprc: int | None = None
    stck_hgpr: int | None = None
    stck_lwpr: int | None = None
    stck_clpr: int | None = None
    acml_vol: int | None = None
    acml_tr_pbmn: int | None = None
    flng_cls_code: str | None = None
    prtt_rate: float | None = None
    mod_yn: str | None = None
    prdy_vrss_sign: str | None = None
    prdy_vrss: int | None = None
    revl_issu_reas: str | None = None

    model_config = ConfigDict(extra="ignore")


class PeriodicPriceResponse(BaseModel):
    code: str
    market: str
    period: str
    start_date: str
    end_date: str
    adj_price: bool
    source: str
    count: int
    prices: list[PeriodicPricePoint] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class CurrentPriceResponse(BaseModel):
    code: str
    market: str
    source: str
    price: dict[str, Any] = Field(default_factory=dict)
    updated_at: str | None = None

    model_config = ConfigDict(extra="ignore")


class CombinedPriceDetail(BaseModel):
    price: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    model_config = ConfigDict(extra="ignore")


class BestPrice(BaseModel):
    exchange: str | None = None
    price: int | None = None
    source: dict[str, Any] | None = None

    model_config = ConfigDict(extra="ignore")


class CombinedPriceResponse(BaseModel):
    code: str
    krx: CombinedPriceDetail
    nxt: CombinedPriceDetail
    best: BestPrice
    active_exchanges: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")
