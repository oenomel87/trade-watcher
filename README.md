# Trade Watcher

한국투자증권 API를 활용한 실시간 주식 모니터링 및 관심목록 관리 시스템입니다. 

본 프로젝트는 주식 시세를 자동으로 수집하고 관리하는 **Backend Engine**과, 이를 편리하게 조회하고 제어할 수 있는 **CLI 기반 인터페이스**로 구성되어 있습니다.

---

## 🏗 프로젝트 구조 (Architecture)

프로젝트는 크게 두 개의 독립적인 패키지로 구성되어 있습니다.

### 1. [Watcher Engine](./watcher-engine) (Backend)
FastAPI 기반의 REST API 서버입니다.
- **주요 기능**: KIS(한국투자증권) API 연동, 주식 시세 캐싱(SQLite), 관심목록 및 폴더 관리.
- **핵심 기술**: Python 3.13, FastAPI, SQLite, uv.
- **구성**:
    - `app/`: API 라우터 및 비즈니스 로직 (Service Layer).
    - `db/`: 데이터베이스 모델 및 연결 관리.
    - `external/`: KIS API 클라이언트 및 인증 모듈.
    - `loaders/`: 종목 정보 파싱 및 DB 로드 유틸리티.

### 2. [Watcher CLI](./watcher-cli) (Frontend)
kubectl 스타일의 직관적인 명령줄 도구입니다.
- **주요 기능**: 관심목록 조회/생성/삭제, 종목 검색, 실시간 시세 대시보드 (`-w` 모드).
- **핵심 기술**: Python 3.13, argparse, httpx, pydantic.

---

## 🚀 시작하기 (Quick Start)

모든 패키지는 [uv](https://docs.astral.sh/uv/) 패키지 관리자를 사용하여 관리됩니다.

### 1. 사전 요구사항
- Python 3.13 이상
- uv 설치

### 2. Engine 설정 및 실행
```bash
cd watcher-engine

# 의존성 설치
uv sync

# 환경 변수 설정 (.env 파일 작성)
# KIS_APP_KEY, KIS_APP_SECRET 설정 필요
cp .env.sample .env

# 서버 실행 (기본: http://localhost:8000)
uv run uvicorn app.main:app --reload
```

### 3. CLI 설정 및 사용
```bash
cd watcher-cli

# 의존성 설치
uv sync

# 관심목록 조회
uv run main.py watchlists

# 특정 관심목록 실시간 모니터링 (2초 간격)
uv run main.py items --watchlist 1 -w --interval 2
```

---

## 💻 주요 기능 및 사용법 (Key Features)

### 1. 관심목록 (Watchlists) 관리
```bash
# 목록 조회
watcher watchlists

# 이름으로 검색
watcher watchlists --search "보유"

# 새 관심목록 생성
watcher watchlists create --name "배당주" --description "고배당 종목 모음"
```

### 2. 종목 및 시세 조회
```bash
# 종목 검색
watcher stocks -q "삼성전자"

# 관심목록 내 종목 상세 조회 (캐시 기반)
watcher items --watchlist 1

# 실시간 시세 업데이트 모드
watcher items --watchlist 1 -w
```

---

## 📁 디렉토리 설명

- `watcher-engine/`: 백엔드 엔진 소스 코드 및 데이터 로더.
- `watcher-cli/`: CLI 도구 소스 코드.
- `docs/`: 디자인 설계 문서, API 명세, 참고 데이터.
- `data/`: 로컬 SQLite 데이터베이스 파일 (git 제외).

---

## 🔐 보안 및 설정

- **KIS API 인증**: 한국투자증권에서 발급받은 AppKey와 Secret을 `watcher-engine/.env` 파일에 기록해야 합니다.
- **데이터 저장**: 주식 마스터 데이터와 캐시된 시세는 `watcher-engine/data/stocks.db`에 SQLite 형식으로 저장됩니다.

---

## 📝 라이선스
MIT License
