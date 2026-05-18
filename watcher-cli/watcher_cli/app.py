from __future__ import annotations

import argparse
import asyncio

from watcher_cli.catalog import StockCatalog
from watcher_cli.models import CatalogEntry, WatchItem
from watcher_cli.quotes import QuoteService
from watcher_cli.storage import JsonWatchlistStorage
from watcher_cli.terminal import ScreenRenderer, render_monitor, render_watchlist


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    storage = JsonWatchlistStorage()

    if args.command == "list":
        print(render_watchlist(storage.list_items()))
        return

    if args.command == "add":
        _run_add(storage, args.query)
        return

    if args.command == "remove":
        _run_remove(storage, args.query)
        return

    if args.command == "monitor":
        try:
            asyncio.run(_run_monitor(storage, args.interval))
        except KeyboardInterrupt:
            print("\n중단되었습니다.")
        except ValueError as exc:
            print(str(exc))
            raise SystemExit(1) from exc
        return

    parser.error("지원하지 않는 명령입니다.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="watcher", description="단일 목록 기반 시세 모니터")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="저장된 관심 종목 목록")

    add_parser = subparsers.add_parser("add", help="관심 종목 추가")
    add_parser.add_argument("query", nargs="?", help="종목 코드 또는 이름")

    remove_parser = subparsers.add_parser("remove", help="관심 종목 제거")
    remove_parser.add_argument("query", nargs="?", help="종목 코드 또는 이름")

    monitor_parser = subparsers.add_parser("monitor", help="5초 주기 시세 모니터")
    monitor_parser.add_argument("--interval", type=float, default=5.0, help="갱신 주기(초)")

    return parser


def _run_add(storage: JsonWatchlistStorage, query: str | None) -> None:
    catalog = StockCatalog.from_default_files()
    if query is None:
        query = input("검색어 입력: ").strip()
        if not query:
            print("취소되었습니다.")
            return

    matches = catalog.search(query)
    selected = _choose_catalog_entry(matches)
    if selected is None:
        return

    item = WatchItem(
        symbol=selected.symbol,
        name=selected.name,
        market=selected.market,
        exchange=selected.exchange,
        aliases=selected.aliases,
    )
    added = storage.add(item)
    if not added:
        print("이미 저장된 종목입니다.")
        return
    print(f"추가됨: {item.symbol} {item.name}")


def _run_remove(storage: JsonWatchlistStorage, query: str | None) -> None:
    items = storage.list_items()
    if not items:
        print("저장된 관심 종목이 없습니다.")
        return

    if query is None:
        for index, item in enumerate(items, start=1):
            print(f"{index}. {item.symbol} {item.name}")
        selected = _choose_watch_item(items)
        if selected is None:
            return
        removed = storage.remove(selected.symbol)
    else:
        removed = storage.remove(query)

    if removed is None:
        print("삭제할 종목을 찾을 수 없습니다.")
        return

    print(f"삭제됨: {removed.symbol} {removed.name}")


async def _run_monitor(storage: JsonWatchlistStorage, interval: float) -> None:
    service: QuoteService | None = None
    renderer = ScreenRenderer()
    renderer.start()
    try:
        while True:
            items = storage.list_items()
            if not items:
                quotes = []
            else:
                if service is None:
                    service = QuoteService()
                quotes = await service.fetch_many(items)
            renderer.render(render_monitor(quotes))
            await asyncio.sleep(interval)
    finally:
        renderer.stop()
        if service is not None:
            await service.close()


def _choose_catalog_entry(matches: list[CatalogEntry]) -> CatalogEntry | None:
    if not matches:
        print("검색 결과가 없습니다.")
        return None
    if len(matches) == 1:
        return matches[0]

    for index, entry in enumerate(matches, start=1):
        exchange = f" ({entry.exchange})" if entry.exchange else ""
        print(f"{index}. {entry.symbol} {entry.name}{exchange}")
    selected = _read_index(len(matches))
    if selected is None:
        print("취소되었습니다.")
        return None
    return matches[selected]


def _choose_watch_item(items: list[WatchItem]) -> WatchItem | None:
    selected = _read_index(len(items))
    if selected is None:
        return None
    return items[selected]


def _read_index(count: int) -> int | None:
    try:
        raw = input("번호 선택: ").strip()
    except EOFError:
        return None
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        print("숫자를 입력하세요.")
        return None
    if value < 1 or value > count:
        print("범위를 벗어난 번호입니다.")
        return None
    return value - 1
