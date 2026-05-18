from __future__ import annotations

from pathlib import Path

from watcher_cli.models import CatalogEntry


class StockCatalog:
    FILE_CONFIG = [
        ("kospi_code.txt", "KR", "KRX", "fixed"),
        ("kosdaq_code.txt", "KR", "KRX", "fixed"),
        ("nxt_kospi_code.txt", "KR", "NXT", "fixed"),
        ("nxt_kosdaq_code.txt", "KR", "NXT", "fixed"),
        ("nasdaq.txt", "US", "NAS", "us_tab"),
        ("nyse.txt", "US", "NYS", "us_tab"),
    ]

    CODE_START = 0
    CODE_END = 9
    NAME_START = 21
    STANDARD_CODE_END = 21
    FIXED_SUFFIX_LEN = 228
    US_FIELD_COUNT = 24
    US_EXCHANGE = 2
    US_SYMBOL = 4
    US_KOREAN_NAME = 6
    US_ENGLISH_NAME = 7

    def __init__(self, entries: list[CatalogEntry]):
        self.entries = entries

    @classmethod
    def from_default_files(cls) -> StockCatalog:
        data_dir = Path(__file__).resolve().parents[2] / "docs" / "stocks"
        entries: list[CatalogEntry] = []
        for filename, market, exchange, line_format in cls.FILE_CONFIG:
            path = data_dir / filename
            if not path.exists():
                continue
            with path.open("rb") as handle:
                for line in handle:
                    entry = cls._parse_line(line, market, exchange, line_format)
                    if entry is not None:
                        entries.append(entry)
        return cls.from_entries(entries)

    @classmethod
    def from_entries(cls, entries: list[CatalogEntry]) -> StockCatalog:
        normalized: dict[tuple[str, str], CatalogEntry] = {}
        for entry in entries:
            key = (entry.market, entry.symbol)
            if entry.market == "KR":
                normalized[key] = CatalogEntry(
                    symbol=entry.symbol,
                    name=entry.name,
                    market=entry.market,
                    exchange=None,
                )
                continue
            normalized[key] = entry
        return cls(sorted(normalized.values(), key=lambda item: (item.market, item.symbol)))

    def search(self, query: str, limit: int = 20) -> list[CatalogEntry]:
        normalized = query.strip().lower()
        exact = [
            entry
            for entry in self.entries
            if (
                entry.symbol.lower() == normalized
                or entry.name.lower() == normalized
                or normalized in {alias.lower() for alias in entry.aliases}
            )
        ]
        if exact:
            return exact[:limit]

        partial = [
            entry
            for entry in self.entries
            if (
                normalized in entry.symbol.lower()
                or normalized in entry.name.lower()
                or any(normalized in alias.lower() for alias in entry.aliases)
            )
        ]
        return partial[:limit]

    @classmethod
    def _parse_line(
        cls,
        line: bytes,
        market: str,
        exchange: str,
        line_format: str,
    ) -> CatalogEntry | None:
        if line_format == "us_tab":
            return cls._parse_us_line(line, market, exchange)
        return cls._parse_fixed_line(line, market, exchange)

    @classmethod
    def _parse_fixed_line(cls, line: bytes, market: str, exchange: str) -> CatalogEntry | None:
        name_end = len(line) - cls.FIXED_SUFFIX_LEN
        if name_end <= cls.NAME_START:
            return None
        try:
            symbol = line[cls.CODE_START : cls.CODE_END].decode("utf-8").strip()
            name = line[cls.NAME_START:name_end].decode("utf-8").strip()
        except UnicodeDecodeError:
            return None
        if not symbol or not name:
            return None
        return CatalogEntry(symbol=symbol, name=name, market=market, exchange=exchange)

    @classmethod
    def _parse_us_line(cls, line: bytes, market: str, exchange: str) -> CatalogEntry | None:
        try:
            text = line.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError:
            return None
        fields = text.split("\t")
        if len(fields) < cls.US_FIELD_COUNT:
            return None
        symbol = fields[cls.US_SYMBOL].strip()
        english_name = fields[cls.US_ENGLISH_NAME].strip()
        korean_name = fields[cls.US_KOREAN_NAME].strip()
        name = english_name or korean_name
        actual_exchange = fields[cls.US_EXCHANGE].strip() or exchange
        if not symbol or not name:
            return None
        aliases = tuple(alias for alias in [korean_name] if alias and alias != name)
        return CatalogEntry(
            symbol=symbol,
            name=name,
            market=market,
            exchange=actual_exchange,
            aliases=aliases,
        )
