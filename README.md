# Trade Watcher

한국투자증권 OpenAPI를 직접 호출해서 관심 종목 단일 목록을 관리하고, 터미널에서 주기적으로 시세를 보여주는 개인용 CLI 도구입니다.

## Quick Start

사전 요구사항:

- Python 3.13 이상
- `uv`
- 한국투자증권 OpenAPI 자격 증명

설치 및 실행:

```bash
cd watcher-cli
uv sync

export KIS_APP_KEY=your_app_key
export KIS_APP_SECRET=your_app_secret
export KIS_IS_REAL=false

uv run python main.py --help
```

## Main Commands

```bash
# 저장된 목록 보기
uv run python main.py list

# 종목 추가/삭제
uv run python main.py add 삼성전자
uv run python main.py remove 삼성전자

# 대화형 추가/삭제
uv run python main.py add
uv run python main.py remove

# 5초 주기 모니터
uv run python main.py monitor
uv run python main.py monitor --interval 2
```

## Behavior

- 관심 종목은 단일 목록 1개만 지원합니다.
- 목록 저장 위치는 `~/.config/trade-watcher/watchlist.json` 입니다.
- 한국 종목은 `KRX`와 `NXT`를 함께 조회하고, 화면에는 `최적가`, `KRX`, `NXT`, `변동률`이 표시됩니다.
- 미국 종목은 단일 현재가만 표시됩니다.
- 별도 `watcher-engine` 서버는 필요하지 않습니다.

## Repository Layout

- `watcher-cli/`: 현재 사용되는 CLI 구현
- `watcher-engine/`: 이전 구조 기반 코드. 현재 단순 CLI 런타임에는 필수 아님
- `docs/`: 종목 마스터 파일과 설계 문서

## License

MIT License
