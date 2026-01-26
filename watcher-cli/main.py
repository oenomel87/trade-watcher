from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import sys
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
    items.add_argument("--market", help="시장 코드 (기본값: 설정값)")
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

    stocks = subparsers.add_parser("stocks", help="종목 검색")
    stocks.add_argument("-q", "--query", required=True, help="검색어(종목명 또는 코드)")
    stocks.add_argument("--limit", type=int, help="검색 개수 (기본값: 20)")

    prices = subparsers.add_parser("prices", help="종목 시세 조회")
    prices.add_argument("stock_code", help="종목 코드")
    prices.add_argument("--no-cache", action="store_true", help="캐시 사용 안 함")
    prices.add_argument("-w", "--watch", action="store_true", help="주기적으로 새로 고침")
    prices.add_argument("--interval", type=float, help="갱신 주기(초)")

    parser._watcher_subparsers = {  # type: ignore[attr-defined]
        "help": help_parser,
        "watchlists": watchlists,
        "items": items,
        "stocks": stocks,
        "prices": prices,
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
        try:
            results = await client.search_stocks(args.query, limit=args.limit or 20)
        except EngineAPIError as exc:
            _print_error(f"종목 검색에 실패했습니다: {exc.message}")
            return

        if not results:
            print("검색 결과가 없습니다.")
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
        while True:
            _clear_screen()
            print(f"{title} (갱신: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            await render()
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
        row = [
            item.stock_code,
            name,
            _format_number(item.current_price),
            _format_signed(item.change),
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


def _clear_screen() -> None:
    print("\033c", end="")


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
