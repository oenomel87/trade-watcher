"""Stock parser tests for KR/US listings."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from loaders.stock_parser import StockParser  # noqa: E402

DATA_DIR = ROOT_DIR.parent / "docs" / "stocks"


def _read_first_line(path: Path) -> bytes:
    with path.open("rb") as f:
        return f.readline()


def test_parse_korean_and_us_lines():
    parser = StockParser(data_dir=str(DATA_DIR))

    kospi_line = _read_first_line(DATA_DIR / "kospi_code.txt")
    nasdaq_line = _read_first_line(DATA_DIR / "nasdaq.txt")

    kr_stock = parser.parse_line(kospi_line, "KOSPI", "KRX")
    assert kr_stock is not None
    assert kr_stock.market == "KOSPI"
    assert kr_stock.exchange == "KRX"
    assert kr_stock.code
    assert kr_stock.name

    us_stock = parser.parse_us_line(nasdaq_line, "US", "US")
    assert us_stock is not None
    assert us_stock.market == "US"
    assert us_stock.exchange == "US"

    fields = nasdaq_line.decode("utf-8").rstrip("\r\n").split("\t")
    assert us_stock.code == fields[4].strip()
    assert us_stock.standard_code == fields[5].strip()
    assert us_stock.name == (fields[6].strip() or fields[7].strip())


def test_parse_all_includes_kr_and_us():
    parser = StockParser(data_dir=str(DATA_DIR))
    stocks = parser.parse_all()

    assert any(s.market == "US" and s.exchange == "US" for s in stocks)
    assert any(s.market == "KOSPI" and s.exchange in {"KRX", "NXT"} for s in stocks)
    assert any(s.market == "KOSDAQ" and s.exchange in {"KRX", "NXT"} for s in stocks)
