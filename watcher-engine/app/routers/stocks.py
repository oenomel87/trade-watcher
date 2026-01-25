"""종목 API 라우터"""

from fastapi import APIRouter, HTTPException, Query

from app.services.stock_current_price_service import StockCurrentPriceService
from app.services.stock_price_service import StockPriceService
from app.services.stock_service import StockService
from external.client import APIError


router = APIRouter()


@router.get("")
async def list_stocks(
    market: str | None = Query(None, description="시장 필터 (KOSPI/KOSDAQ)"),
    exchange: str | None = Query(None, description="거래소 필터 (KRX/NXT)"),
    limit: int = Query(100, ge=1, le=1000, description="조회 개수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
):
    """
    종목 목록 조회

    - **market**: KOSPI 또는 KOSDAQ
    - **exchange**: KRX 또는 NXT
    - **limit**: 조회 개수 (최대 1000)
    - **offset**: 페이징 오프셋
    """
    service = StockService()
    stocks = service.get_stocks(
        market=market, exchange=exchange, limit=limit, offset=offset
    )
    return {"stocks": stocks, "count": len(stocks)}


@router.get("/stats")
async def get_stats():
    """종목 통계 조회"""
    service = StockService()
    return service.get_stats()


@router.get("/search")
async def search_stocks(
    q: str = Query(..., min_length=1, description="검색어 (종목명 또는 코드)"),
    limit: int = Query(20, ge=1, le=100, description="조회 개수"),
):
    """
    종목 검색

    - **q**: 검색어 (종목명 또는 코드에서 검색)
    """
    service = StockService()
    stocks = service.search_stocks(query=q, limit=limit)
    return {"stocks": stocks, "count": len(stocks)}


@router.get("/{code}")
async def get_stock(code: str):
    """
    종목 상세 조회

    - **code**: 종목 코드 (예: 005930)
    """
    service = StockService()
    stock = service.get_stock_by_code(code)

    if not stock:
        raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {code}")

    return stock


@router.get("/{code}/prices/periodic")
async def get_periodic_prices(
    code: str,
    start_date: str = Query(..., description="조회 시작일 (YYYYMMDD 또는 YYYY-MM-DD)"),
    end_date: str = Query(..., description="조회 종료일 (YYYYMMDD 또는 YYYY-MM-DD)"),
    period: str = Query("D", description="기간 구분 (D/W/M/Y)"),
    market: str = Query("J", description="시장 구분 (J/NX/UN)"),
    adj_price: bool = Query(True, description="수정주가 여부 (True: 수정주가)"),
    use_cache: bool = Query(True, description="DB 캐시 사용 여부"),
):
    """
    종목 기간별 시세 조회

    - **code**: 종목 코드 (예: 005930)
    - **start_date**: 조회 시작일 (YYYYMMDD)
    - **end_date**: 조회 종료일 (YYYYMMDD)
    - **period**: D(일)/W(주)/M(월)/Y(년)
    """
    service = StockPriceService()
    try:
        return service.get_periodic_prices(
            stock_code=code,
            start_date=start_date,
            end_date=end_date,
            period=period,
            market=market,
            adj_price=adj_price,
            use_cache=use_cache,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except APIError as exc:
        detail = {"message": str(exc), "response": exc.response}
        raise HTTPException(status_code=502, detail=detail) from exc


@router.get("/{code}/prices/current")
async def get_current_price(
    code: str,
    market: str = Query("J", description="시장 구분 (J/NX/UN)"),
    use_cache: bool = Query(False, description="DB 캐시 사용 여부"),
    max_age_sec: int | None = Query(None, ge=0, description="캐시 허용 최대 경과초"),
):
    """
    종목 현재가 조회

    - **code**: 종목 코드 (예: 005930)
    - **market**: J(KRX)/NX(NXT)/UN(통합)
    """
    service = StockCurrentPriceService()
    try:
        return service.get_current_price(
            stock_code=code,
            market=market,
            use_cache=use_cache,
            max_age_sec=max_age_sec,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except APIError as exc:
        detail = {"message": str(exc), "response": exc.response}
        raise HTTPException(status_code=502, detail=detail) from exc


@router.post("/load")
async def load_stocks():
    """
    종목 데이터 로드

    docs/stocks 폴더의 파일에서 종목 정보를 읽어 DB에 저장합니다.
    """
    service = StockService()
    result = service.load_stocks_from_files()
    return {
        "message": "종목 데이터 로드 완료",
        **result,
    }
