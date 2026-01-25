"""종목 코드 파일 파서."""
from pathlib import Path

from db.models import Stock


class StockParser:
    """종목 코드 파일 파서.

    고정 길이 필드 형식의 종목 파일을 파싱합니다.
    """

    # 파일 설정: (파일명, 시장, 거래소)
    FILE_CONFIG = [
        ("kospi_code.txt", "KOSPI", "KRX"),
        ("kosdaq_code.txt", "KOSDAQ", "KRX"),
        ("nxt_kospi_code.txt", "KOSPI", "NXT"),
        ("nxt_kosdaq_code.txt", "KOSDAQ", "NXT"),
    ]

    # 필드 위치 (0-indexed)
    CODE_START = 0
    CODE_END = 9
    STANDARD_CODE_START = 9
    STANDARD_CODE_END = 21
    NAME_START = 21
    NAME_END = 61

    def __init__(self, data_dir: str = "../docs/stocks"):
        """파서 초기화.

        Args:
            data_dir: 종목 파일이 있는 디렉토리 경로
        """
        self.data_dir = Path(data_dir)

    def parse_line(self, line: bytes, market: str, exchange: str) -> Stock | None:
        """한 줄(바이트)을 파싱하여 Stock 객체 반환.

        Args:
            line: 파일의 한 줄 (바이트)
            market: 시장 (KOSPI/KOSDAQ)
            exchange: 거래소 (KRX/NXT)

        Returns:
            Stock 객체 또는 None (파싱 실패 시)
        """
        if len(line) < self.NAME_END:
            return None

        try:
            code = line[self.CODE_START : self.CODE_END].decode("utf-8").strip()
            standard_code = line[self.STANDARD_CODE_START : self.STANDARD_CODE_END].decode("utf-8").strip()
            name = line[self.NAME_START : self.NAME_END].decode("utf-8").strip()
        except UnicodeDecodeError:
            return None

        if not code or not name:
            return None

        return Stock(
            code=code,
            standard_code=standard_code,
            name=name,
            market=market,
            exchange=exchange,
        )

    def parse_file(self, filename: str, market: str, exchange: str) -> list[Stock]:
        """파일을 파싱하여 종목 리스트 반환.

        Args:
            filename: 파일명
            market: 시장
            exchange: 거래소

        Returns:
            Stock 객체 리스트
        """
        file_path = self.data_dir / filename
        stocks = []

        if not file_path.exists():
            print(f"⚠️  파일을 찾을 수 없습니다: {file_path}")
            return stocks

        with open(file_path, "rb") as f:
            for line in f:
                stock = self.parse_line(line, market, exchange)
                if stock:
                    stocks.append(stock)

        return stocks

    def parse_all(self) -> list[Stock]:
        """모든 종목 파일을 파싱.

        Returns:
            전체 Stock 객체 리스트
        """
        all_stocks = []

        for filename, market, exchange in self.FILE_CONFIG:
            stocks = self.parse_file(filename, market, exchange)
            print(f"📄 {filename}: {len(stocks):,}개 종목 파싱")
            all_stocks.extend(stocks)

        return all_stocks
