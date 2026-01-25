"""데이터베이스 모델 정의."""
from dataclasses import dataclass


@dataclass
class Stock:
    """종목 정보 모델."""

    code: str  # 단축 종목코드 (예: 005930)
    standard_code: str  # 표준코드 (예: KR7005930003)
    name: str  # 종목명 (예: 삼성전자)
    market: str  # 시장 (KOSPI/KOSDAQ)
    exchange: str  # 거래소 (KRX/NXT)


@dataclass
class StockListing:
    """거래소 상장 정보 모델."""

    stock_code: str  # 종목코드 (예: 005930)
    exchange: str  # 거래소 (KRX/NXT)
    is_primary: int  # 대표 거래소 여부 (1: 대표)


@dataclass
class StockPricePeriodic:
    """기간별 시세 데이터 모델."""

    stock_code: str  # 종목코드 (예: 005930)
    market: str  # 시장 코드 (J/NX/UN)
    period: str  # 기간 코드 (D/W/M/Y)
    adj_price: int  # 수정주가 여부 (0: 수정주가, 1: 원주가)
    business_date: str  # 영업일자 (YYYYMMDD)
    open_price: int | None
    high_price: int | None
    low_price: int | None
    close_price: int | None
    volume: int | None
    trade_amount: int | None
    flng_cls_code: str | None
    prtt_rate: float | None
    mod_yn: str | None
    prdy_vrss_sign: str | None
    prdy_vrss: int | None
    revl_issu_reas: str | None
