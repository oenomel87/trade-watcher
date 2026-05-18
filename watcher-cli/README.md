# Watcher CLI

한국투자증권 OpenAPI를 직접 호출해서 관심 종목 단일 목록을 관리하고, 터미널에서 시세를 주기적으로 보여주는 CLI입니다.

## Setup

```bash
cd watcher-cli
uv sync
```

필수 환경 변수:

```bash
export KIS_APP_KEY=your_app_key
export KIS_APP_SECRET=your_app_secret
export KIS_IS_REAL=true
```

또는 `.env.sample`을 복사해서 `watcher-cli/.env`를 만들 수 있습니다.

```bash
cd watcher-cli
cp .env.sample .env
```

CLI는 현재 작업 디렉터리의 `.env`를 먼저 읽고, 없으면 `watcher-cli/.env`를 읽습니다.

## Run

```bash
cd watcher-cli
uv run python main.py --help
```

## Commands

```bash
# 저장된 목록 보기
uv run python main.py list

# 종목 추가
uv run python main.py add 삼성전자
uv run python main.py add 005930
uv run python main.py add

# 종목 제거
uv run python main.py remove 삼성전자
uv run python main.py remove 005930
uv run python main.py remove

# 5초 주기 모니터
uv run python main.py monitor

# 주기 변경
uv run python main.py monitor --interval 2
```

## Behavior

- 관심 종목은 단일 목록 1개만 지원합니다.
- 저장 파일은 `~/.config/trade-watcher/watchlist.json` 입니다.
- 한국 종목은 `monitor`에서 항상 `KRX`와 `NXT`를 함께 조회합니다.
- 화면에는 `최적가`, `KRX`, `NXT`, `변동률`이 표시됩니다.
- 미국 종목은 단일 현재가만 표시되며 `KRX`, `NXT` 컬럼은 `-`로 표시됩니다.

## Notes

- `add` 는 로컬 종목 마스터(`../docs/stocks`)를 읽어 코드/이름 검색을 지원합니다.
- 한국 종목은 거래소별 중복을 합쳐 하나의 논리 종목으로 저장합니다.
- 별도 `watcher-engine` 서버는 필요하지 않습니다.
