# Single-CLI Monitor Design

Date: 2026-04-08
Status: Approved in conversation

## Summary

Trade Watcher를 개인용 터미널 도구로 단순화한다. 앞으로 필요한 핵심 기능은 세 가지다.

1. 한국투자증권 OpenAPI OAuth 인증으로 시세를 조회한다.
2. 모니터링할 관심 종목을 단일 목록 하나에 저장한다.
3. CLI에서 기본 5초 간격으로 시세를 갱신해 출력한다.

기존의 다중 watchlist, folder, REST API 서버, 기간별 시세 조회, 해외/국내 부가 기능 대부분은 이번 범위에서 제거한다.

## Goals

- 별도 서버 없이 `watcher` CLI 하나로 동작한다.
- 관심 종목 목록은 단일 목록 1개만 지원한다.
- `monitor`는 한국 종목의 `KRX`와 `NXT`를 항상 함께 조회한다.
- `monitor`는 한국 종목에 대해 `최적가`를 메인으로, `KRX/NXT`를 보조 컬럼으로 표시한다.
- 종목 추가/삭제는 짧은 명령 방식과 대화형 방식을 둘 다 지원한다.
- 실행 경로에 따라 동작이 달라지지 않도록 로컬 저장과 설정 경로를 고정한다.

## Non-Goals

- 다중 watchlist / folder 구조
- FastAPI 기반 `watcher-engine` 런타임
- CLI와 엔진 사이의 HTTP 통신
- 기간별 시세 조회
- NXT 표시를 켜고 끄는 별도 flag
- 원격 다중 사용자 지원

## Product Shape

런타임 제품은 `watcher-cli` 단일 프로그램으로 합친다.

- 사용자는 `watcher list`, `watcher add`, `watcher remove`, `watcher monitor`만 사용한다.
- CLI가 직접 KIS 인증, 종목 검색, 관심 목록 저장, 현재가 조회, 터미널 렌더링을 담당한다.
- `watcher-engine`은 더 이상 필수 런타임 컴포넌트가 아니다.

이 설계의 기준은 "개인용 터미널 모니터"다. 여러 클라이언트를 위한 공용 API는 제공하지 않는다.

## Commands

### `watcher list`

저장된 단일 관심 종목 목록을 출력한다.

### `watcher add <query>`

짧은 명령 방식이다.

- 입력값이 정확한 종목코드면 바로 후보를 찾는다.
- 입력값이 이름/부분 문자열이면 로컬 종목 마스터에서 후보를 찾는다.
- 후보가 1개면 바로 추가한다.
- 후보가 여러 개면 선택 목록을 보여주고 하나를 고르게 한다.

### `watcher add`

대화형 방식이다.

- 검색어 입력
- 후보 표시
- 번호 선택
- 단일 목록에 저장

### `watcher remove <query>`

짧은 명령 방식이다.

- 코드 또는 이름으로 저장 목록에서 항목을 찾는다.
- 정확히 1개면 바로 삭제한다.
- 여러 개면 선택 목록을 보여주고 삭제 대상을 고르게 한다.

### `watcher remove`

대화형 방식이다.

- 저장된 목록을 번호와 함께 보여준다.
- 삭제할 항목을 선택한다.

### `watcher monitor`

가장 중요한 명령이다.

- 기본 갱신 주기는 5초다.
- 저장된 단일 관심 종목 목록을 읽는다.
- 각 종목의 현재가를 주기적으로 조회한다.
- 같은 터미널 화면을 갱신한다.

### `watcher monitor --interval <sec>`

갱신 주기를 바꾼다. 기본값은 5초다.

## Internal Structure

CLI 내부는 아래 다섯 책임으로 나눈다.

- `auth`: KIS OAuth 토큰 발급, 만료 확인, 재사용
- `storage`: 단일 관심 종목 목록 읽기/쓰기
- `catalog`: 로컬 종목 마스터 검색
- `quotes`: 국내/해외 현재가 조회와 응답 정규화
- `commands`: `list`, `add`, `remove`, `monitor` 명령 오케스트레이션
- `terminal`: 표 렌더링과 화면 갱신

중요한 제약은 다음과 같다.

- `commands`는 파일이나 HTTP를 직접 다루지 않는다.
- `commands.monitor`는 `storage`, `quotes`, `terminal`을 조합해 주기 실행을 오케스트레이션한다.
- 한국 종목의 `KRX/NXT` 통합 판단은 `quotes`가 맡는다.

## Storage Design

관심 종목 저장은 SQLite가 아니라 JSON 파일 1개로 단순화한다.

기본 경로:

- `~/.config/trade-watcher/watchlist.json`

예시 구조:

```json
{
  "version": 1,
  "items": [
    {
      "symbol": "005930",
      "name": "삼성전자",
      "market": "KR"
    },
    {
      "symbol": "AAPL",
      "name": "Apple",
      "market": "US",
      "exchange": "NAS"
    }
  ]
}
```

저장 필드는 최소만 유지한다.

- `symbol`
- `name`
- `market`
- `exchange` (미국 종목 등 추가 힌트가 필요한 경우만)

목록은 하나뿐이며, 같은 종목이 중복 저장되지 않도록 한다.

## Credential and Config

KIS 인증 정보는 CLI가 직접 읽는다.

- `KIS_APP_KEY`
- `KIS_APP_SECRET`
- `KIS_IS_REAL`

이번 범위에서는 별도 설정 파일을 두지 않는다. 인증은 환경 변수만 사용하고, 모니터 주기 변경은 명령행 옵션으로만 받는다.

모니터 주기 기본값은 5초다.

## Stock Catalog

`add` 편의 기능을 위해 로컬 종목 마스터를 유지한다.

- 국내 종목은 기존 KOSPI/KOSDAQ/NXT 파일을 재사용할 수 있다.
- 미국 종목은 기존 NASDAQ/NYSE 파일을 재사용할 수 있다.
- 검색은 코드와 이름 둘 다 지원한다.

국내 종목은 카탈로그 단계에서 거래소별 중복을 합치고, 종목코드 기준의 단일 논리 종목으로 정규화한다. 즉, `watcher add 삼성전자`에서 `KRX용 삼성전자`와 `NXT용 삼성전자`를 따로 고르게 하지 않는다.

이 카탈로그는 조회용 읽기 전용 자산이다. 시세 캐시나 별도 DB는 만들지 않는다.

## Quote Behavior

### Korean stocks

한국 종목은 항상 `KRX`와 `NXT`를 함께 조회한다.

화면 컬럼:

- `최적가`
- `KRX`
- `NXT`
- `변동률`

`최적가`는 기존 규칙을 유지한다.

- 둘 중 하나만 유효하면 그 값을 사용
- 둘 다 유효하면 거래량 기준으로 선택

사용자는 별도 flag 없이 항상 두 시장 정보를 본다.

### US stocks

미국 종목은 단일 거래소 현재가만 보여준다.

- `최적가` 컬럼에 단일 현재가를 넣는다.
- `KRX`, `NXT` 보조 컬럼은 `-`로 표시한다.

## Monitor Output

예시:

```text
코드      이름        최적가     KRX       NXT       변동률
005930   삼성전자    72,100    72,000    72,100    +0.84%
000660   SK하이닉스  201,500   201,500   201,300   -0.21%
AAPL     Apple       214.33    -         -         +1.12%
```

출력 규칙:

- 같은 화면을 갱신한다.
- 한 종목 조회 실패가 전체 모니터를 중단시키지 않는다.
- 실패한 종목은 가격 대신 오류 표시를 남긴다.

## Error Handling

- 인증 실패 시 전체 명령을 실패시키고 원인을 보여준다.
- `add/remove`에서 후보가 없으면 명확한 안내를 출력한다.
- `monitor`에서는 종목별 실패를 허용하고 다음 종목을 계속 조회한다.
- 한국 종목에서 `NXT`만 실패해도 `KRX`가 살아 있으면 `최적가`는 계속 계산한다.
- 저장 파일이 없으면 빈 목록으로 초기화한다.
- 저장 파일이 깨졌으면 복구를 유도하는 에러를 보여준다.

## Testing

최소 테스트 범위는 다음과 같다.

- `storage`: 생성, 추가, 삭제, 중복 방지
- `catalog`: 코드 검색, 이름 검색, 다중 후보 처리
- `quotes`: 한국 종목 KRX/NXT 결합, 미국 종목 단일 가격 처리, 부분 실패 처리
- `commands`: `add/remove/list/monitor` 인자 해석
- `terminal`: 모니터 표 렌더링

실시간 외부 API 테스트는 최소화하고, KIS 클라이언트는 테스트 더블로 교체한다.

## Migration Direction

구현 계획에서는 아래 순서로 단순화한다.

1. CLI가 직접 사용할 공용 모듈을 만든다.
2. 단일 목록 저장과 직접 KIS 조회 경로를 붙인다.
3. `monitor`를 새 구조 위에서 유지한다.
4. 기존 watchlist/folder/API 의존 명령을 제거한다.
5. 문서를 새 사용 방식으로 정리한다.

이번 설계의 목표는 기능 추가가 아니라 기능 축소와 구조 단순화다.
