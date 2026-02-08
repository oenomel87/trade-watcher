from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.portfolio_service import PortfolioService

router = APIRouter()


class BuyRequest(BaseModel):
    stock_code: str
    quantity: int
    price: float
    buy_date: str  # YYYY-MM-DD
    memo: Optional[str] = None


class SellRequest(BaseModel):
    stock_code: str
    quantity: int
    price: float
    sell_date: str  # YYYY-MM-DD
    memo: Optional[str] = None


@router.post("/buy", tags=["Portfolio"])
async def buy_stock(request: BuyRequest):
    """주식 매수 - 새로운 Lot 생성"""
    service = PortfolioService()
    try:
        result = service.buy_stock(
            stock_code=request.stock_code,
            quantity=request.quantity,
            price=request.price,
            buy_date=request.buy_date,
            memo=request.memo,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sell", tags=["Portfolio"])
async def sell_stock(request: SellRequest):
    """주식 매도 - FIFO 계산 및 실현 손익 기록"""
    service = PortfolioService()
    try:
        result = service.sell_stock(
            stock_code=request.stock_code,
            quantity=request.quantity,
            price=request.price,
            sell_date=request.sell_date,
            memo=request.memo,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/holdings", tags=["Portfolio"])
async def get_holdings():
    """현재 보유 중인 종목 목록 조회"""
    service = PortfolioService()
    holdings = service.get_holdings()
    return {"success": True, "data": holdings}


@router.get("/pnl", tags=["Portfolio"])
async def get_pnl_summary():
    """포트폴리오 손익 요약 조회"""
    service = PortfolioService()
    summary = service.get_pnl_summary()
    return {"success": True, "data": summary}


@router.get("/trades", tags=["Portfolio"])
async def get_trades(
    stock_code: Optional[str] = None,
    trade_type: Optional[str] = None,
):
    """거래 내역 조회

    - stock_code: 종목 코드 필터 (선택)
    - trade_type: BUY 또는 SELL 필터 (선택)
    """
    service = PortfolioService()
    trades = service.get_trades(stock_code=stock_code, trade_type=trade_type)
    trades_dict = [
        {
            "id": t.id,
            "stock_code": t.stock_code,
            "trade_type": t.trade_type,
            "quantity": t.quantity,
            "price": t.price,
            "trade_date": t.trade_date,
            "realized_pnl": t.realized_pnl,
            "matched_lots": t.matched_lots,
            "memo": t.memo,
            "created_at": t.created_at,
        }
        for t in trades
    ]
    return {"success": True, "data": trades_dict}
