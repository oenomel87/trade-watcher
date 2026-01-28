# Watcher CLI

관심목록을 조회하고 종목 정보를 출력하는 CLI입니다.

## Setup

```bash
cd watcher-cli
uv sync
```

## Run

```bash
uv run python main.py watchlists
```

## Alias Setup (Recommended)

매번 긴 명령어를 입력하는 대신 단축어(Alias)를 설정하면 편리합니다. `~/.zshrc` (또는 `~/.bash_profile`)에 다음 내용을 추가하세요:

```bash
# trade-watcher alias
alias tw='uv --directory /Users/yspark/workspace/toy/trade-watcher/watcher-cli run python main.py'
```

이후 `source ~/.zshrc`를 수행하면 어디서든 `tw` 명령어로 실행할 수 있습니다:

```bash
tw watchlists
tw prices 005930 -w
```

엔진이 별도로 실행 중이어야 합니다:

```bash
cd watcher-engine
uv run python -m app.main
```

## Usage

```bash
# 관심목록 목록
uv run python main.py watchlists

# 도움말
uv run python main.py help
uv run python main.py help watchlists
uv run python main.py help items
uv run python main.py --help

# 관심목록 검색
uv run python main.py watchlists --search 관심

# 종목 검색
uv run python main.py stocks --query 삼성

# KRX/NXT 통합 시세 조회
uv run python main.py prices 005930
uv run python main.py prices 005930 -w --interval 2

# 관심목록 생성/삭제
uv run python main.py watchlists create --name "장기투자" --description "장기 보유"
uv run python main.py watchlists delete --watchlist "장기투자"

# 관심목록 종목 조회 (ID)
uv run python main.py items --watchlist 1

# 관심목록 종목 조회 (이름)
uv run python main.py items --watchlist "장기투자"

# 실시간 갱신 (-w)
uv run python main.py items --watchlist 1 -w --interval 2

# NXT 시세 함께 조회 (--include-nxt)
uv run python main.py items --watchlist 1 --include-nxt

# 종목 추가/삭제
uv run python main.py items add --watchlist 1 --stock-code 005930 --memo "삼성전자"
uv run python main.py items delete --watchlist 1 --item-id 3
uv run python main.py items delete --watchlist 1 --stock-code 005930
```

## Interactive Commands (대화형 명령)

CLI는 대화형 모드도 지원합니다.

### Monitor (모니터링 대시보드)

```bash
# 대화형 모니터링 시작 (기본 관심목록)
uv run python main.py monitor

# 특정 관심목록으로 시작
uv run python main.py monitor --watchlist 1

# NXT 시세 포함
uv run python main.py monitor --include-nxt
```

**단축키:**
| 키 | 동작 |
|----|------|
| `q` | 종료 |
| `n` | NXT 시세 표시 토글 |
| `r` | 즉시 새로고침 |
| `1`-`9` | 해당 번호의 관심목록으로 전환 |

### Add Wizard (종목 추가 마법사)

```bash
# 단계별 종목 추가 시작
uv run python main.py add
```

마법사가 안내하는 단계:
1. 관심목록 선택 (번호 입력)
2. 종목 검색 및 선택
3. 메모 입력 (선택사항)
4. 확인 후 추가

참고:
- 폴더는 CLI에서 다루지 않으며, 종목 추가 시 기본 폴더로 저장됩니다.
- 현재가 캐시가 없으면 실시간 조회를 시도합니다. (`--no-refresh-missing`으로 비활성화 가능)


## Configuration

Config search order:

1) `watcher-cli/cli_config.json`
2) `watcher-cli/tui_config.json` (호환용)
3) `$XDG_CONFIG_HOME/trade-watcher/cli_config.json`
4) `$XDG_CONFIG_HOME/trade-watcher/tui_config.json` (호환용)
5) `~/.config/trade-watcher/cli_config.json`
6) `~/.config/trade-watcher/tui_config.json` (호환용)

Environment variables override the config file:

- `WATCHER_ENGINE_URL`
- `WATCHER_CLI_REFRESH_SEC` (또는 `WATCHER_TUI_REFRESH_SEC`)
- `WATCHER_CLI_SUMMARY_CACHE_SEC` (또는 `WATCHER_TUI_SUMMARY_CACHE_SEC`)
- `WATCHER_CLI_MARKET` (또는 `WATCHER_TUI_MARKET`)
- `WATCHER_CLI_DEFAULT_WATCHLIST_ID` (또는 `WATCHER_TUI_DEFAULT_WATCHLIST_ID`)

Example config:

```json
{
  "engine_url": "http://localhost:9944",
  "refresh_interval_sec": 2,
  "summary_cache_age_sec": 60,
  "market": "J",
  "default_watchlist_id": null
}
```
