"""
Trade Watcher Engine API Server

FastAPI 기반 주식 거래 모니터링 API 서버
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import stocks
from app.routers import watchlists
from db import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행"""
    # 시작 시: DB 테이블 생성
    db = Database()
    db.connect()
    db.create_tables()
    db.close()
    print("✅ Database initialized")
    yield
    # 종료 시
    print("👋 Shutting down...")


app = FastAPI(
    title="Trade Watcher Engine",
    description="한국투자증권 API를 활용한 주식 거래 모니터링 API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
app.include_router(watchlists.router, prefix="/watchlists", tags=["WatchLists"])


@app.get("/", tags=["Health"])
async def root():
    """헬스 체크"""
    return {"status": "ok", "service": "Trade Watcher Engine"}


@app.get("/health", tags=["Health"])
async def health_check():
    """상세 헬스 체크"""
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import os
    from pathlib import Path

    from dotenv import load_dotenv
    import uvicorn

    # .env 파일 로드
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    port = int(os.getenv("WATCHER_ENGINE_PORT", "9944"))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)
