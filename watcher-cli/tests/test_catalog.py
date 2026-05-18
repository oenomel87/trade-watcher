from watcher_cli.catalog import StockCatalog
from watcher_cli.models import CatalogEntry


def test_catalog_merges_korean_exchange_duplicates():
    catalog = StockCatalog.from_entries(
        [
            CatalogEntry(symbol="005930", name="삼성전자", market="KR", exchange="KRX"),
            CatalogEntry(symbol="005930", name="삼성전자", market="KR", exchange="NXT"),
            CatalogEntry(symbol="AAPL", name="Apple", market="US", exchange="NAS"),
        ]
    )

    results = catalog.search("삼성")

    assert len(results) == 1
    assert results[0] == CatalogEntry(
        symbol="005930",
        name="삼성전자",
        market="KR",
        exchange=None,
    )


def test_catalog_keeps_us_exchange_information():
    catalog = StockCatalog.from_entries(
        [
            CatalogEntry(symbol="AAPL", name="Apple", market="US", exchange="NAS"),
        ]
    )

    results = catalog.search("AAPL")

    assert results == [
        CatalogEntry(symbol="AAPL", name="Apple", market="US", exchange="NAS")
    ]


def test_parse_us_line_prefers_english_name_when_available():
    fields = [""] * 24
    fields[2] = "NAS"
    fields[4] = "AAPL"
    fields[6] = "애플"
    fields[7] = "Apple"
    line = ("\t".join(fields) + "\n").encode("utf-8")

    entry = StockCatalog._parse_us_line(line, "US", "NAS")

    assert entry == CatalogEntry(
        symbol="AAPL",
        name="Apple",
        market="US",
        exchange="NAS",
        aliases=("애플",),
    )


def test_catalog_search_matches_us_korean_alias():
    catalog = StockCatalog.from_entries(
        [
            CatalogEntry(
                symbol="AAPL",
                name="Apple",
                market="US",
                exchange="NAS",
                aliases=("애플",),
            )
        ]
    )

    results = catalog.search("애플")

    assert results == [
        CatalogEntry(
            symbol="AAPL",
            name="Apple",
            market="US",
            exchange="NAS",
            aliases=("애플",),
        )
    ]
