# Trade Watcher Engine

한국투자증권 API를 활용한 주식 거래 모니터링 엔진

## 📋 요구사항

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (패키지 관리자)

## 🚀 시작하기

### 1. 의존성 설치

```bash
cd watcher-engine
uv sync
```

### 2. 환경 변수 설정

`.env` 파일에 한국투자증권 API 키를 설정합니다:

```env
KIS_APP_KEY=your_app_key
KIS_APP_SECRET=your_app_secret
KIS_IS_REAL=false  # true: 실전, false: 모의
```

### 3. 서버 실행

```bash
uv run python -m app.main
```

서버 실행 후:
- API 문서: http://localhost:9944/docs
- 헬스 체크: http://localhost:9944/

> `.env` 파일의 `WATCHER_ENGINE_PORT` 환경 변수로 포트를 변경할 수 있습니다.

## 📁 프로젝트 구조

```
watcher-engine/
├── app/                      # FastAPI 애플리케이션
│   ├── main.py               # 앱 진입점
│   ├── routers/              # API 라우터
│   │   └── stocks.py         # 종목 API
│   └── services/             # 비즈니스 로직
│       └── stock_service.py
├── core/                     # 핵심 설정
│   └── config.py             # 환경 변수 로드
├── db/                       # 데이터베이스
│   ├── database.py           # SQLite 연결 관리
│   └── models.py             # 데이터 모델
├── external/                 # 외부 API 클라이언트
│   ├── auth.py               # 토큰 관리
│   ├── client.py             # HTTP 클라이언트
│   └── kis/                  # 한국투자증권 API
│       └── client.py
├── loaders/                  # 데이터 로더
│   └── stock_parser.py       # 종목 파일 파서 (KOSPI/KOSDAQ/US)
└── data/                     # SQLite DB 저장소
    └── stocks.db
```

## 🔌 API 엔드포인트

### 헬스 체크

```bash
GET /
GET /health
```

### 종목 API

`market` 파라미터는 `KOSPI`, `KOSDAQ`, `US` 중 하나를 사용합니다.

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/stocks` | 종목 목록 조회 |
| GET | `/stocks/stats` | 종목 통계 |
| GET | `/stocks/search?q={query}` | 종목 검색 |
| GET | `/stocks/{code}` | 종목 상세 조회 |
| GET | `/stocks/{code}/prices/periodic` | 종목 기간별 시세 조회 |
| GET | `/stocks/{code}/prices/current` | 종목 현재가 조회 |
| GET | `/stocks/{code}/prices/combined` | KRX/NXT 통합 시세 조회 |
| POST | `/stocks/load` | 종목 데이터 로드 |

### Watch list API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/watchlists` | watch list 목록 |
| POST | `/watchlists` | watch list 생성 (기본 폴더 포함) |
| GET | `/watchlists/{watchlist_id}` | watch list 상세 |
| DELETE | `/watchlists/{watchlist_id}` | watch list 삭제 |
| GET | `/watchlists/{watchlist_id}/folders` | 폴더 목록 |
| POST | `/watchlists/{watchlist_id}/folders` | 폴더 생성 |
| PATCH | `/watchlists/{watchlist_id}/folders/{folder_id}` | 폴더 수정 |
| DELETE | `/watchlists/{watchlist_id}/folders/{folder_id}` | 폴더 삭제 |
| GET | `/watchlists/{watchlist_id}/items` | 종목 목록 |
| GET | `/watchlists/{watchlist_id}/items/summary` | 종목 + 현재가 요약 |
| POST | `/watchlists/{watchlist_id}/items` | 종목 추가 |
| DELETE | `/watchlists/{watchlist_id}/items/{item_id}` | 종목 삭제 |

### 예시

```bash
# 종목 목록 (KOSPI, 10개)
curl "http://localhost:9944/stocks?market=KOSPI&limit=10"

# 종목 목록 (US, 10개)
curl "http://localhost:9944/stocks?market=US&limit=10"

# 종목 검색
curl "http://localhost:9944/stocks/search?q=삼성"

# 종목 상세
curl "http://localhost:9944/stocks/005930"

# 종목 기간별 시세 (일봉)
curl "http://localhost:9944/stocks/005930/prices/periodic?start_date=20240101&end_date=20240131&period=D"

# 종목 현재가
curl "http://localhost:9944/stocks/005930/prices/current?market=J"

# 종목 통계
curl "http://localhost:9944/stocks/stats"

# watch list 생성
curl -X POST "http://localhost:9944/watchlists?name=관심종목&description=장기투자"

# watch list 폴더 생성
curl -X POST "http://localhost:9944/watchlists/1/folders?name=반도체&description=메모리"

# watch list 종목 추가 (폴더 지정)
curl -X POST "http://localhost:9944/watchlists/1/items?stock_code=005930&folder_id=2&memo=삼성전자"

# watch list 종목 추가 (최상위)
curl -X POST "http://localhost:9944/watchlists/1/items?stock_code=000660"

# watch list 종목 요약 (현재가, 거래량, 등락폭)
curl "http://localhost:9944/watchlists/1/items/summary?use_cache=true&max_age_sec=60"

# watch list 종목 요약 (NXT 시세 포함)
curl "http://localhost:9944/watchlists/1/items/summary?include_nxt=true"

# KRX/NXT 통합 시세 조회
curl "http://localhost:9944/stocks/005930/prices/combined"
```

## 🔑 외부 API 사용

한국투자증권 API 클라이언트 사용 예시:

```python
from external.kis import KISClient
from core.config import load_config

config = load_config()
client = KISClient(config)

# 토큰은 자동으로 관리됨
token_info = client.get_token_info()
print(f"Token expires at: {token_info.expired_at}")
```

## 📊 데이터베이스

SQLite를 사용하며, `data/stocks.db`에 저장됩니다.

### Stock 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | Primary Key |
| code | TEXT | 종목 코드 (UNIQUE) |
| standard_code | TEXT | 표준 코드 |
| name | TEXT | 종목명 |
| market | TEXT | 시장 (KOSPI/KOSDAQ/US) |
| exchange | TEXT | 대표 거래소 (KRX/NXT/US) |

### StockListings 테이블

거래소별 상장 정보를 관리합니다. 동일 종목이 KRX/NXT에 동시에 존재할 수 있습니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | Primary Key |
| stock_code | TEXT | 종목 코드 |
| exchange | TEXT | 거래소 (KRX/NXT/US) |
| is_primary | INTEGER | 대표 거래소 여부 |

## ⏰ 거래 시간 정보 (NXT)

NXT(넥스트레이드)는 아래 시간대에 거래가 가능합니다.

- **장전(프리마켓)**: 08:00 ~ 08:50
- **정규장(메인마켓)**: 09:00:30 ~ 15:20
- **장후(애프터마켓)**: 15:40 ~ 20:00 (NXT 전용)

## 📝 License

MIT
