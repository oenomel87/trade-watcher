from __future__ import annotations

import argparse
import asyncio
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import io
import select
import sys
import termios
import tty
from typing import Any

from watcher_cli.client import EngineAPIError, EngineClient
from watcher_cli.config import CliConfig, load_config
from watcher_cli.models import Watchlist, WatchlistItemSummary


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except Exception as exc:
        print(f"설정 로드에 실패했습니다: {exc}")
        raise SystemExit(1) from exc

    if args.engine_url:
        config = config.model_copy(update={"engine_url": args.engine_url})

    try:
        if args.command == "help":
            _print_help(parser, args.topic)
        elif args.command == "watchlists":
            if args.watchlists_command == "create":
                asyncio.run(_run_watchlist_create(args, config))
            elif args.watchlists_command == "delete":
                asyncio.run(_run_watchlist_delete(args, config))
            else:
                asyncio.run(_run_watchlists(args, config))
        elif args.command == "items":
            if args.items_command == "add":
                asyncio.run(_run_item_add(args, config))
            elif args.items_command == "delete":
                asyncio.run(_run_item_delete(args, config))
            else:
                asyncio.run(_run_items(args, config))
        elif args.command == "stocks":
            asyncio.run(_run_stock_search(args, config))
        elif args.command == "prices":
            asyncio.run(_run_combined_price(args, config))
        elif args.command == "monitor":
            asyncio.run(_run_monitor(args, config))
        elif args.command == "overseas":
            asyncio.run(_run_overseas(args, config))
        elif args.command == "add":
            asyncio.run(_run_add_wizard(args, config))
        else:
            print("지원하지 않는 명령입니다.")
            raise SystemExit(2)
    except KeyboardInterrupt:
        print("\n중단되었습니다.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="watcher",
        description="관심목록을 조회하고 종목 정보를 출력하는 CLI",
    )
    parser.add_argument("--config", help="설정 파일 경로 (선택)")
    parser.add_argument("--engine-url", help="엔진 API 주소 (선택)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    help_parser = subparsers.add_parser("help", help="도움말 출력")
    help_parser.add_argument("topic", nargs="?", help="명령어 이름 (watchlists/items)")

    watchlists = subparsers.add_parser("watchlists", help="관심목록 목록 조회")
    watchlists.add_argument("-s", "--search", help="관심목록 이름 검색어")
    watchlists.add_argument("-w", "--watch", action="store_true", help="주기적으로 새로 고침")
    watchlists.add_argument("--interval", type=float, help="갱신 주기(초)")
    watchlists_sub = watchlists.add_subparsers(dest="watchlists_command", required=False)
    watchlists_create = watchlists_sub.add_parser("create", help="관심목록 생성")
    watchlists_create.add_argument("--name", required=True, help="관심목록 이름")
    watchlists_create.add_argument("--description", help="설명(선택)")
    watchlists_delete = watchlists_sub.add_parser("delete", help="관심목록 삭제")
    watchlists_delete.add_argument("--watchlist", required=True, help="관심목록 ID 또는 이름")

    common_items = argparse.ArgumentParser(add_help=False)
    common_items.add_argument("-l", "--watchlist", help="관심목록 ID 또는 이름")

    items = subparsers.add_parser("items", help="관심목록 종목 목록 조회", parents=[common_items])
    items.add_argument("--market", help="시장 코드 (J/NX/UN, 기본값: 설정값)")
    items.add_argument("--max-age-sec", type=int, help="캐시 허용 최대 경과초")
    items.add_argument("--no-cache", action="store_true", help="캐시 사용 안 함")
    items.add_argument(
        "--refresh-missing",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="캐시 미스 시 실시간 조회 (기본값: 사용)",
    )
    items.add_argument("-w", "--watch", action="store_true", help="주기적으로 새로 고침")
    items.add_argument("--interval", type=float, help="갱신 주기(초)")
    items.add_argument("--include-nxt", action="store_true", help="NXT 시세 함께 조회")

    items_sub = items.add_subparsers(dest="items_command", required=False)
    items_add = items_sub.add_parser("add", help="관심목록 종목 추가", parents=[common_items])
    items_add.add_argument("--stock-code", required=True, help="종목 코드")
    items_add.add_argument("--memo", help="메모(선택)")
    items_delete = items_sub.add_parser("delete", help="관심목록 종목 삭제", parents=[common_items])
    items_delete.add_argument("--item-id", type=int, help="항목 ID")
    items_delete.add_argument("--stock-code", help="종목 코드(선택)")

    stocks = subparsers.add_parser("stocks", help="종목 검색/목록")
    stocks.add_argument("-q", "--query", help="검색어(종목명 또는 코드)")
    stocks.add_argument("--market", help="시장 필터 (KOSPI/KOSDAQ/US)")
    stocks.add_argument("--exchange", help="거래소 필터 (KRX/NXT/US)")
    stocks.add_argument("--limit", type=int, help="조회 개수 (검색: 기본값 20, 목록: 기본값 100)")
    stocks.add_argument("--offset", type=int, help="목록 조회 시작 위치 (기본값: 0)")

    prices = subparsers.add_parser("prices", help="종목 시세 조회")
    prices.add_argument("stock_code", help="종목 코드")
    prices.add_argument("--no-cache", action="store_true", help="캐시 사용 안 함")
    prices.add_argument("-w", "--watch", action="store_true", help="주기적으로 새로 고침")
    prices.add_argument("--interval", type=float, help="갱신 주기(초)")

    monitor = subparsers.add_parser("monitor", help="대화형 모니터링 대시보드")
    monitor.add_argument("-l", "--watchlist", help="시작할 관심목록 ID 또는 이름")
    monitor.add_argument("--interval", type=float, help="갱신 주기(초)")
    monitor.add_argument("--include-nxt", action="store_true", help="NXT 시세 함께 조회")

    overseas = subparsers.add_parser("overseas", help="해외주식/지수 시세 조회")
    overseas.add_argument("symbol", help="종목/지수 코드 (예: TSLA, .DJI)")
    overseas.add_argument("--exchange", "-e", default="NAS", help="거래소 코드 (NAS/NYS, 기본값: NAS)")
    overseas.add_argument("--periodic", action="store_true", help="기간별 시세 조회")
    overseas.add_argument("--start-date", help="조회 시작일 (YYYYMMDD)")
    overseas.add_argument("--end-date", help="조회 종료일 (YYYYMMDD)")
    overseas.add_argument("--period", default="D", help="기간 구분 (D/W/M/Y, 기본값: D)")
    overseas.add_argument("--market-code", default="N", help="시장 구분 (N:지수/X:환율/I:국채/S:금선물, 기본값: N)")
    overseas.add_argument("-w", "--watch", action="store_true", help="주기적으로 새로 고침")
    overseas.add_argument("--interval", type=float, help="갱신 주기(초)")

    add_wizard = subparsers.add_parser("add", help="대화형 종목 추가 마법사")

    parser._watcher_subparsers = {  # type: ignore[attr-defined]
        "help": help_parser,
        "watchlists": watchlists,
        "items": items,
        "stocks": stocks,
        "prices": prices,
        "monitor": monitor,
        "overseas": overseas,
        "add": add_wizard,
    }

    return parser


async def _run_watchlists(args: argparse.Namespace, config: CliConfig) -> None:
    async with EngineClient(config.engine_url) as client:
        interval = args.interval or config.refresh_interval_sec

        async def render() -> None:
            try:
                watchlists = await client.list_watchlists()
            except EngineAPIError as exc:
                _print_error(f"관심목록 조회에 실패했습니다: {exc.message}")
                return

            rows = _filter_watchlists(watchlists, args.search)
            _print_watchlist_table(rows)

        if args.watch:
            await _watch_loop(render, interval, title="관심목록")
        else:
            await render()


async def _run_items(args: argparse.Namespace, config: CliConfig) -> None:
    async with EngineClient(config.engine_url) as client:
        interval = args.interval or config.refresh_interval_sec
        market = args.market or config.market

        try:
            watchlist = await _resolve_watchlist(client, args.watchlist, config.default_watchlist_id)
        except EngineAPIError as exc:
            _print_error(f"관심목록 조회에 실패했습니다: {exc.message}")
            return
        if watchlist is None:
            if args.watchlist is None and config.default_watchlist_id is None:
                _print_error("관심목록을 지정하세요. (--watchlist)")
            else:
                _print_error("관심목록을 찾을 수 없습니다.")
            return

        name_cache: dict[str, str] = {}

        async def render() -> None:
            try:
                items = await client.list_items_summary(
                    watchlist_id=watchlist.id,
                    use_cache=not args.no_cache,
                    max_age_sec=args.max_age_sec if args.max_age_sec is not None else config.summary_cache_age_sec,
                    refresh_missing=args.refresh_missing,
                    market=market,
                    include_nxt=args.include_nxt,
                )
            except EngineAPIError as exc:
                _print_error(f"종목 조회에 실패했습니다: {exc.message}")
                return

            await _fill_stock_names(client, items, name_cache)
            _print_item_table(watchlist, items, name_cache, include_nxt=args.include_nxt)

        if args.watch:
            await _watch_loop(render, interval, title="종목 목록")
        else:
            await render()


async def _run_watchlist_create(args: argparse.Namespace, config: CliConfig) -> None:
    async with EngineClient(config.engine_url) as client:
        try:
            created = await client.create_watchlist(
                name=args.name,
                description=args.description,
            )
        except EngineAPIError as exc:
            _print_error(f"관심목록 생성에 실패했습니다: {exc.message}")
            return

        print(f"관심목록 생성 완료: {created.name} (ID: {created.id})")


async def _run_watchlist_delete(args: argparse.Namespace, config: CliConfig) -> None:
    async with EngineClient(config.engine_url) as client:
        try:
            watchlist = await _resolve_watchlist(client, args.watchlist, config.default_watchlist_id)
        except EngineAPIError as exc:
            _print_error(f"관심목록 조회에 실패했습니다: {exc.message}")
            return

        if watchlist is None:
            _print_error("관심목록을 찾을 수 없습니다.")
            return

        try:
            await client.delete_watchlist(watchlist.id)
        except EngineAPIError as exc:
            _print_error(f"관심목록 삭제에 실패했습니다: {exc.message}")
            return

        print(f"관심목록 삭제 완료: {watchlist.name} (ID: {watchlist.id})")


async def _run_item_add(args: argparse.Namespace, config: CliConfig) -> None:
    async with EngineClient(config.engine_url) as client:
        try:
            watchlist = await _resolve_watchlist(client, args.watchlist, config.default_watchlist_id)
        except EngineAPIError as exc:
            _print_error(f"관심목록 조회에 실패했습니다: {exc.message}")
            return
        if watchlist is None:
            _print_error("관심목록을 찾을 수 없습니다.")
            return

        folder_id = await _get_default_folder_id(client, watchlist.id)

        try:
            await client.add_item(
                watchlist_id=watchlist.id,
                stock_code=args.stock_code,
                folder_id=folder_id,
                memo=args.memo,
            )
        except EngineAPIError as exc:
            _print_error(f"종목 추가에 실패했습니다: {exc.message}")
            return

        print(f"종목 추가 완료: {args.stock_code}")


async def _run_item_delete(args: argparse.Namespace, config: CliConfig) -> None:
    async with EngineClient(config.engine_url) as client:
        try:
            watchlist = await _resolve_watchlist(client, args.watchlist, config.default_watchlist_id)
        except EngineAPIError as exc:
            _print_error(f"관심목록 조회에 실패했습니다: {exc.message}")
            return
        if watchlist is None:
            _print_error("관심목록을 찾을 수 없습니다.")
            return

        item_id = args.item_id
        if item_id is None and args.stock_code:
            try:
                items = await client.list_items_summary(
                    watchlist_id=watchlist.id,
                    use_cache=True,
                    max_age_sec=config.summary_cache_age_sec,
                    refresh_missing=False,
                    market=config.market,
                )
            except EngineAPIError as exc:
                _print_error(f"종목 조회에 실패했습니다: {exc.message}")
                return

            matches = [item for item in items if item.stock_code == args.stock_code]
            if len(matches) == 1:
                item_id = matches[0].id
            elif len(matches) > 1:
                _print_error("동일한 종목이 여러 개 있습니다. --item-id를 지정하세요.")
                return
            else:
                _print_error("종목을 찾을 수 없습니다.")
                return

        if item_id is None:
            _print_error("--item-id 또는 --stock-code를 지정하세요.")
            return

        try:
            await client.delete_item(watchlist.id, item_id)
        except EngineAPIError as exc:
            _print_error(f"종목 삭제에 실패했습니다: {exc.message}")
            return

        print(f"종목 삭제 완료: item_id={item_id}")


async def _run_stock_search(args: argparse.Namespace, config: CliConfig) -> None:
    async with EngineClient(config.engine_url) as client:
        if args.query:
            try:
                results = await client.search_stocks(args.query, limit=args.limit or 20)
            except EngineAPIError as exc:
                _print_error(f"종목 검색에 실패했습니다: {exc.message}")
                return
        else:
            try:
                results = await client.list_stocks(
                    market=args.market,
                    exchange=args.exchange,
                    limit=args.limit or 100,
                    offset=args.offset or 0,
                )
            except EngineAPIError as exc:
                _print_error(f"종목 목록 조회에 실패했습니다: {exc.message}")
                return

        if args.query:
            if args.market:
                results = [
                    stock for stock in results
                    if (stock.market or "").upper() == args.market.upper()
                ]
            if args.exchange:
                results = [
                    stock for stock in results
                    if (stock.exchange or "").upper() == args.exchange.upper()
                ]

        if not results:
            print("검색 결과가 없습니다." if args.query else "표시할 종목이 없습니다.")
            return

        rows = [
            [stock.code, stock.name, stock.market or "", stock.exchange or ""]
            for stock in results
        ]
        _print_table(["코드", "종목명", "시장", "거래소"], rows)


async def _run_combined_price(args: argparse.Namespace, config: CliConfig) -> None:
    async with EngineClient(config.engine_url) as client:
        interval = args.interval or config.refresh_interval_sec
        stock_code = args.stock_code

        name_cache: dict[str, str] = {}

        async def render() -> None:
            try:
                stock = await client.get_stock(stock_code)
                name_cache[stock.code] = stock.name
                
                result = await client.get_combined_price(
                    code=stock_code,
                    use_cache=not args.no_cache,
                )
            except EngineAPIError as exc:
                _print_error(f"시세 조회에 실패했습니다: {exc.message}")
                return

            _print_combined_price(result, name_cache.get(stock_code, "알 수 없음"))

        if args.watch:
            await _watch_loop(render, interval, title=f"[{stock_code}] 통합 시세")
        else:
            await render()


async def _run_monitor(args: argparse.Namespace, config: CliConfig) -> None:
    """Interactive monitoring dashboard with keyboard controls."""
    async with EngineClient(config.engine_url) as client:
        interval = args.interval or config.refresh_interval_sec
        include_nxt = args.include_nxt

        try:
            watchlists = await client.list_watchlists()
        except EngineAPIError as exc:
            _print_error(f"관심목록 조회에 실패했습니다: {exc.message}")
            return

        if not watchlists:
            _print_error("관심목록이 없습니다.")
            return

        # Select initial watchlist
        current_watchlist = await _resolve_watchlist(client, args.watchlist, config.default_watchlist_id)
        if current_watchlist is None:
            current_watchlist = watchlists[0]

        name_cache: dict[str, str] = {}

        async def render() -> None:
            try:
                items = await client.list_items_summary(
                    watchlist_id=current_watchlist.id,
                    use_cache=False,
                    refresh_missing=True,
                    market=config.market,
                    include_nxt=include_nxt,
                )
            except EngineAPIError as exc:
                _print_error(f"종목 조회에 실패했습니다: {exc.message}")
                return

            await _fill_stock_names(client, items, name_cache)
            _print_item_table(current_watchlist, items, name_cache, include_nxt=include_nxt)
            nxt_label = " [NXT]" if include_nxt else ""
            print(f"\n단축키: q=종료  n=NXT토글  r=새로고침  1-9=관심목록전환{nxt_label}")

        # Monitoring loop with key detection
        previous_lines = 0
        try:
            while True:
                # Build title with status
                title = f"모니터링: {current_watchlist.name}"
                output = await _capture_output(render, title)
                output, line_count = _normalize_output(output)
                _render_in_place(output, previous_lines)
                previous_lines = line_count

                key = await _read_key_with_timeout(interval)
                
                if key == 'q':
                    print("\n종료합니다.")
                    return
                elif key == 'n':
                    include_nxt = not include_nxt
                elif key == 'r':
                    pass  # Just refresh
                elif key and key.isdigit():
                    idx = int(key) - 1
                    if 0 <= idx < len(watchlists):
                        current_watchlist = watchlists[idx]

        except KeyboardInterrupt:
            print("\n중단되었습니다.")



async def _run_overseas(args: argparse.Namespace, config: CliConfig) -> None:
    """해외주식/지수 시세 조회."""
    async with EngineClient(config.engine_url) as client:
        interval = args.interval or config.refresh_interval_sec
        symbol = args.symbol.upper()

        if args.periodic:
            # 기간별 시세 조회
            if not args.start_date or not args.end_date:
                _print_error("기간별 조회는 --start-date와 --end-date가 필요합니다.")
                return

            async def render_periodic() -> None:
                try:
                    result = await client.get_overseas_periodic_prices(
                        symbol=symbol,
                        start_date=args.start_date,
                        end_date=args.end_date,
                        period=args.period,
                        market_code=args.market_code,
                    )
                except EngineAPIError as exc:
                    _print_error(f"기간별 시세 조회에 실패했습니다: {exc.message}")
                    return

                _print_overseas_periodic(result)

            if args.watch:
                await _watch_loop(render_periodic, interval, title=f"[{symbol}] 기간별 시세")
            else:
                await render_periodic()
        else:
            # 현재가 조회
            async def render_current() -> None:
                try:
                    result = await client.get_overseas_current_price(
                        exchange=args.exchange.upper(),
                        symbol=symbol,
                    )
                except EngineAPIError as exc:
                    _print_error(f"현재가 조회에 실패했습니다: {exc.message}")
                    return

                _print_overseas_current(result)

            if args.watch:
                await _watch_loop(render_current, interval, title=f"[{args.exchange.upper()}:{symbol}] 현재가")
            else:
                await render_current()


async def _run_add_wizard(args: argparse.Namespace, config: CliConfig) -> None:
    """Interactive wizard for adding stocks to watchlist."""
    async with EngineClient(config.engine_url) as client:
        print("\n=== 종목 추가 마법사 ===\n")

        # Step 1: Select watchlist
        print("[1단계] 관심목록 선택")
        print("-" * 40)
        
        try:
            watchlists = await client.list_watchlists()
        except EngineAPIError as exc:
            _print_error(f"관심목록 조회에 실패했습니다: {exc.message}")
            return

        if not watchlists:
            _print_error("관심목록이 없습니다. 먼저 관심목록을 생성하세요.")
            return

        for idx, wl in enumerate(watchlists, 1):
            desc = f"  - {wl.description}" if wl.description else ""
            print(f"  {idx}) {wl.name}{desc}")
        print()

        watchlist_idx = _prompt_number("선택할 번호를 입력하세요", 1, len(watchlists))
        if watchlist_idx is None:
            print("취소되었습니다.")
            return
        
        selected_watchlist = watchlists[watchlist_idx - 1]
        print(f"✓ 선택됨: {selected_watchlist.name}\n")

        # Step 2: Search and select stock
        print("[2단계] 종목 검색")
        print("-" * 40)
        
        query = input("검색어 입력: ").strip()
        if not query:
            print("취소되었습니다.")
            return

        try:
            stocks = await client.search_stocks(query, limit=10)
        except EngineAPIError as exc:
            _print_error(f"종목 검색에 실패했습니다: {exc.message}")
            return

        if not stocks:
            _print_error("검색 결과가 없습니다.")
            return

        print()
        for idx, stock in enumerate(stocks, 1):
            print(f"  {idx}) {stock.code}  {stock.name}")
        print()

        stock_idx = _prompt_number("선택할 번호를 입력하세요", 1, len(stocks))
        if stock_idx is None:
            print("취소되었습니다.")
            return

        selected_stock = stocks[stock_idx - 1]
        print(f"✓ 선택됨: {selected_stock.name} ({selected_stock.code})\n")

        # Step 3: Optional memo
        print("[3단계] 메모 입력 (선택사항, Enter로 스킵)")
        print("-" * 40)
        memo = input("메모: ").strip() or None

        # Confirmation
        print("\n[확인]")
        print("-" * 40)
        print(f"  관심목록: {selected_watchlist.name}")
        print(f"  종목: {selected_stock.name} ({selected_stock.code})")
        if memo:
            print(f"  메모: {memo}")
        print()

        confirm = input("추가하시겠습니까? (y/n): ").strip().lower()
        if confirm != 'y':
            print("취소되었습니다.")
            return

        # Add the item
        folder_id = await _get_default_folder_id(client, selected_watchlist.id)

        try:
            await client.add_item(
                watchlist_id=selected_watchlist.id,
                stock_code=selected_stock.code,
                folder_id=folder_id,
                memo=memo,
            )
        except EngineAPIError as exc:
            _print_error(f"종목 추가에 실패했습니다: {exc.message}")
            return

        print(f"\n✓ 종목 추가 완료: {selected_stock.name} ({selected_stock.code})")


def _filter_watchlists(watchlists: list[Watchlist], query: str | None) -> list[Watchlist]:
    if not query:
        return watchlists
    lowered = query.lower()
    return [wl for wl in watchlists if lowered in wl.name.lower()]


async def _resolve_watchlist(
    client: EngineClient,
    value: str | None,
    default_id: int | None,
) -> Watchlist | None:
    watchlists = await client.list_watchlists()
    if not watchlists:
        return None

    if value is None:
        if default_id is not None:
            for watchlist in watchlists:
                if watchlist.id == default_id:
                    return watchlist
        return None

    if value.isdigit():
        target_id = int(value)
        for watchlist in watchlists:
            if watchlist.id == target_id:
                return watchlist
        return None

    exact = [wl for wl in watchlists if wl.name == value]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        return None

    lowered = value.lower()
    matches = [wl for wl in watchlists if lowered in wl.name.lower()]
    if len(matches) == 1:
        return matches[0]
    return None


async def _fill_stock_names(
    client: EngineClient,
    items: list[WatchlistItemSummary],
    cache: dict[str, str],
) -> None:
    missing = [item.stock_code for item in items if item.stock_code not in cache]
    if not missing:
        return
    tasks = [client.get_stock(code) for code in missing]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            continue
        cache[result.code] = result.name


async def _get_default_folder_id(client: EngineClient, watchlist_id: int) -> int | None:
    try:
        folders = await client.list_folders(watchlist_id)
    except EngineAPIError:
        return None
    if not folders:
        return None

    for folder in folders:
        if getattr(folder, "is_default", False):
            return folder.id

    return folders[0].id


async def _watch_loop(render, interval: float, title: str) -> None:
    try:
        previous_lines = 0
        while True:
            output = await _capture_output(render, title)
            output, line_count = _normalize_output(output)
            _render_in_place(output, previous_lines)
            previous_lines = line_count
            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        return


def _print_watchlist_table(watchlists: list[Watchlist]) -> None:
    if not watchlists:
        print("표시할 관심목록이 없습니다.")
        return

    rows = [
        [str(wl.id), wl.name, wl.description or ""]
        for wl in watchlists
    ]
    _print_table(["ID", "이름", "설명"], rows)


def _print_item_table(
    watchlist: Watchlist,
    items: list[WatchlistItemSummary],
    name_cache: dict[str, str],
    include_nxt: bool = False,
) -> None:
    header = f"관심목록: {watchlist.name} (ID: {watchlist.id})"
    print(header)

    if not items:
        print("표시할 종목이 없습니다.")
        return

    headers = ["코드", "종목명", "현재가", "등락", "등락률", "거래량", "소스"]
    if include_nxt:
        headers.extend(["NXT현재가", "NXT등락", "NXT거래량"])

    rows: list[list[str]] = []
    for item in items:
        name = name_cache.get(item.stock_code) or item.memo or ""
        is_us = (item.market or "").upper() == "US"
        price_text = _format_price(item.current_price) if is_us else _format_number(item.current_price)
        change_text = _format_signed_price(item.change) if is_us else _format_signed(item.change)
        row = [
            item.stock_code,
            name,
            price_text,
            change_text,
            _format_rate(item.change_rate),
            _format_number(item.volume),
            item.price_source or "",
        ]
        if include_nxt:
            row.extend([
                _format_number(item.nxt_current_price),
                _format_signed(item.nxt_change),
                _format_number(item.nxt_volume),
            ])
        rows.append(row)
    _print_table(headers, rows)


def _print_combined_price(result: Any, name: str) -> None:
    print(f"종목: {name} ({result.code})")
    print(f"활성 거래소: {', '.join(result.active_exchanges) or '없음'}")
    print("-" * 40)
    
    # Best Price
    best = result.best
    exchange_label = f"[{best.exchange}]" if best.exchange else "[N/A]"
    print(f"최적가: {exchange_label} {_format_number(best.price)}")
    print("-" * 40)

    # Details
    rows = []
    # KRX
    krx = result.krx
    if krx.error:
        rows.append(["KRX", "오류", krx.error, "-", "-"])
    else:
        p = krx.price
        rows.append([
            "KRX", 
            _format_number(p.get("stck_prpr")), 
            _format_signed(p.get("prdy_vrss")),
            _format_number(p.get("acml_vol")),
            p.get("acml_tr_pbmn") or "-"
        ])
        
    # NXT
    nxt = result.nxt
    if nxt.error:
        rows.append(["NXT", "오류", nxt.error, "-", "-"])
    else:
        p = nxt.price
        rows.append([
            "NXT", 
            _format_number(p.get("stck_prpr")), 
            _format_signed(p.get("prdy_vrss")),
            _format_number(p.get("acml_vol")),
            p.get("acml_tr_pbmn") or "-"
        ])

    _print_table(["거래소", "현재가", "전일대비", "거래량", "거래대금"], rows)


def _print_overseas_current(result: dict) -> None:
    """해외주식 현재가 출력."""
    symbol = result.get("symbol", "")
    exchange = result.get("exchange", "")
    price = result.get("price", {})
    change = result.get("change", {})
    indicators = result.get("indicators", {})
    volume = result.get("volume", {})
    currency = result.get("currency", "")

    print(f"종목: {symbol} ({exchange})")
    print("-" * 40)
    
    # 현재가 정보
    print(f"현재가: {_format_price(price.get('last'))} {currency}")
    print(f"전일종가: {_format_price(price.get('base'))} {currency}")
    print(f"등락: {_format_signed_price(change.get('diff'))} ({_format_rate(change.get('rate'))})")
    print("-" * 40)
    
    # 시고저
    print(f"시가: {_format_price(price.get('open'))}")
    print(f"고가: {_format_price(price.get('high'))}")
    print(f"저가: {_format_price(price.get('low'))}")
    print("-" * 40)
    
    # 거래량
    print(f"거래량: {_format_number(volume.get('current'))}")
    print(f"거래대금: {_format_number(volume.get('amount'))}")
    print("-" * 40)
    
    # 투자지표
    if any([indicators.get("per"), indicators.get("pbr")]):
        print(f"PER: {indicators.get('per') or '-'}")
        print(f"PBR: {indicators.get('pbr') or '-'}")


def _print_overseas_periodic(result: dict) -> None:
    """해외 기간별 시세 출력."""
    symbol = result.get("symbol", "")
    name = result.get("name", "")
    current = result.get("current", {})
    prices = result.get("prices", [])
    count = result.get("count", 0)

    print(f"종목: {name or symbol}")
    print("-" * 50)
    
    # 현재 정보
    if current:
        sign = current.get("change_sign", "")
        sign_label = {"1": "▲", "2": "▲", "3": "=", "4": "▼", "5": "▼"}.get(sign, "")
        print(f"현재가: {_format_price(current.get('price'))} {sign_label}")
        print(f"전일비: {_format_signed_price(current.get('change'))} ({current.get('change_rate') or '-'}%)")
        print("-" * 50)

    # 일자별 시세 테이블
    if prices:
        headers = ["일자", "종가", "시가", "고가", "저가", "거래량"]
        rows = []
        for p in prices[:20]:  # 최대 20개만 표시
            rows.append([
                p.get("date", "-"),
                _format_price(p.get("close")),
                _format_price(p.get("open")),
                _format_price(p.get("high")),
                _format_price(p.get("low")),
                _format_number(p.get("volume")),
            ])
        _print_table(headers, rows)
        if count > 20:
            print(f"... 외 {count - 20}개")
    else:
        print("조회된 데이터가 없습니다.")


def _format_price(value: str | None) -> str:
    """가격 포맷 (소수점 유지)."""
    if value is None or value == "":
        return "-"
    try:
        f = float(value)
        if f == int(f):
            return f"{int(f):,}"
        return f"{f:,.4f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def _format_signed_price(value: str | None) -> str:
    """부호 포함 가격 포맷."""
    if value is None or value == "":
        return "-"
    try:
        f = float(value)
        if f >= 0:
            return f"+{_format_price(str(f))}"
        return f"{_format_price(str(f))}"
    except (TypeError, ValueError):
        return str(value)


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    line = "  ".join(h.ljust(widths[idx]) for idx, h in enumerate(headers))
    print(line)
    print("-" * len(line))

    for row in rows:
        print("  ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)))


def _format_number(value: Any) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{int(float(value)):,}"
    except (TypeError, ValueError):
        return str(value)


def _format_signed(value: Any) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):+.0f}"
    except (TypeError, ValueError):
        return str(value)


def _format_rate(value: Any) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return str(value)


async def _capture_output(render, title: str) -> str:
    buffer = io.StringIO()
    error_buffer = io.StringIO()
    with redirect_stdout(buffer), redirect_stderr(error_buffer):
        print(f"{title} (갱신: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        await render()

    output = buffer.getvalue()
    error_output = error_buffer.getvalue()
    if error_output:
        if output and not output.endswith("\n"):
            output += "\n"
        output += error_output
    return output


def _normalize_output(text: str) -> tuple[str, int]:
    if not text:
        return "", 0
    if not text.endswith("\n"):
        text += "\n"
    return text, text.count("\n")


def _render_in_place(text: str, previous_lines: int) -> None:
    if previous_lines:
        sys.stdout.write(f"\033[{previous_lines}F")
        sys.stdout.write("\033[J")
    sys.stdout.write(text)
    sys.stdout.flush()


def _clear_screen() -> None:
    """Clear the terminal screen."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


async def _read_key_with_timeout(timeout: float) -> str | None:
    """Read a single key with timeout, returns None if no key pressed."""
    loop = asyncio.get_event_loop()
    
    def read_key() -> str | None:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            rlist, _, _ = select.select([sys.stdin], [], [], timeout)
            if rlist:
                return sys.stdin.read(1)
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    return await loop.run_in_executor(None, read_key)


def _prompt_number(prompt: str, min_val: int, max_val: int) -> int | None:
    """Prompt user for a number within range. Returns None on invalid or empty input."""
    try:
        value = input(f"{prompt} ({min_val}-{max_val}): ").strip()
        if not value:
            return None
        num = int(value)
        if min_val <= num <= max_val:
            return num
        print(f"잘못된 입력입니다. {min_val}에서 {max_val} 사이의 숫자를 입력하세요.")
        return None
    except ValueError:
        print("숫자를 입력하세요.")
        return None
    except (EOFError, KeyboardInterrupt):
        return None


def _print_error(message: str) -> None:
    print(message, file=sys.stderr)



def _print_help(parser: argparse.ArgumentParser, topic: str | None) -> None:
    subparsers = getattr(parser, "_watcher_subparsers", {})
    if not topic:
        parser.print_help()
        print("\n예시:")
        print("  watcher watchlists")
        print("  watcher watchlists --search 관심")
        print("  watcher items --watchlist 1")
        print("  watcher items --watchlist 1 -w --interval 2")
        print("  watcher stocks --market US --limit 10")
        return

    subparser = subparsers.get(topic)
    if not subparser:
        print(f"알 수 없는 명령입니다: {topic}")
        print("")
        parser.print_help()
        return

    subparser.print_help()


if __name__ == "__main__":
    main()
