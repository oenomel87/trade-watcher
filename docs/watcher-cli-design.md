# Watcher CLI Design

## 1. 개요 (Overview)

TUI를 제거하고 **kubectl 스타일의 CLI**로 관심목록을 조회합니다.
관심목록 검색, 관심목록 내 종목 조회, `-w` 옵션을 통한 지속 출력 기능을 제공합니다.

## 2. 핵심 명령 (Commands)

### 2.1. 관심목록 목록/검색

```bash
watcher watchlists
watcher watchlists --search 관심
watcher watchlists -w --interval 2
```

### 2.1.1. 종목 검색

```bash
watcher stocks --query 삼성
```

### 2.2. 관심목록 생성/삭제

```bash
watcher watchlists create --name "장기투자" --description "장기 보유"
watcher watchlists delete --watchlist "장기투자"
```

### 2.2. 관심목록 종목 조회

```bash
# ID 기준
watcher items --watchlist 1

# 이름 기준
watcher items --watchlist "장기투자"

# 주기적 갱신
watcher items --watchlist 1 -w --interval 2
```

### 2.3. 관심목록 종목 추가/삭제

```bash
watcher items add --watchlist 1 --stock-code 005930 --memo "삼성전자"
watcher items delete --watchlist 1 --item-id 3
watcher items delete --watchlist 1 --stock-code 005930
```

> 참고: 폴더는 CLI에서 다루지 않으며, 종목 추가 시 기본 폴더로 저장됩니다.

## 3. 출력 포맷 (Output)

- 한국어 컬럼을 기본으로 사용합니다.
- 숫자는 천 단위 구분으로 출력합니다.
- `-w` 모드에서는 화면을 갱신 시간과 함께 반복 출력합니다.

예시:

```
관심목록: 보유종목 (ID: 1)
코드    종목명    현재가   등락   등락률   거래량   소스
--------------------------------------------------------
005930  삼성전자  74,200  +400  +0.54%  1,234,567  kis
```

## 4. Watch 모드 (-w)

- `-w` 옵션 시 지정한 간격으로 계속 갱신합니다.
- 기본 간격은 `refresh_interval_sec` 설정을 따릅니다.
- 현재가 캐시가 없으면 실시간 조회를 시도합니다. (`--no-refresh-missing`으로 비활성화)

## 5. 설정 (Configuration)

### 설정 파일 탐색 순서

1) `watcher-cli/cli_config.json`
2) `watcher-cli/tui_config.json` (호환용)
3) `$XDG_CONFIG_HOME/trade-watcher/cli_config.json`
4) `$XDG_CONFIG_HOME/trade-watcher/tui_config.json` (호환용)
5) `~/.config/trade-watcher/cli_config.json`
6) `~/.config/trade-watcher/tui_config.json` (호환용)

### 환경 변수

- `WATCHER_ENGINE_URL`
- `WATCHER_CLI_REFRESH_SEC` (또는 `WATCHER_TUI_REFRESH_SEC`)
- `WATCHER_CLI_SUMMARY_CACHE_SEC` (또는 `WATCHER_TUI_SUMMARY_CACHE_SEC`)
- `WATCHER_CLI_MARKET` (또는 `WATCHER_TUI_MARKET`)
- `WATCHER_CLI_DEFAULT_WATCHLIST_ID` (또는 `WATCHER_TUI_DEFAULT_WATCHLIST_ID`)

### 예시 설정

```json
{
  "engine_url": "http://localhost:8000",
  "refresh_interval_sec": 2,
  "summary_cache_age_sec": 60,
  "market": "J",
  "default_watchlist_id": null
}
```
