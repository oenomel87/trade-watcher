from __future__ import annotations

from datetime import datetime
from typing import TextIO
import sys

from watcher_cli.models import QuoteSnapshot, WatchItem


def render_watchlist(items: list[WatchItem]) -> str:
    if not items:
        return "저장된 관심 종목이 없습니다."
    rows = [[item.symbol, item.name, item.market, item.exchange or ""] for item in items]
    return _render_table(["코드", "이름", "시장", "거래소"], rows)


def render_monitor(quotes: list[QuoteSnapshot]) -> str:
    title = f"Trade Watcher (갱신: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
    if not quotes:
        return f"{title}\n저장된 관심 종목이 없습니다."

    rows: list[list[str]] = []
    for quote in quotes:
        rows.append(
            [
                quote.symbol,
                quote.name,
                quote.best_price or quote.error or "-",
                quote.krx_price or "-",
                quote.nxt_price or "-",
                _format_rate(quote.change_rate),
            ]
        )

    return f"{title}\n{_render_table(['코드', '이름', '최적가', 'KRX', 'NXT', '변동률'], rows)}"


class ScreenRenderer:
    def __init__(self, stream: TextIO | None = None):
        self.stream = stream or sys.stdout
        self._is_tty = bool(getattr(self.stream, "isatty", lambda: False)())
        self._started = False

    def start(self) -> None:
        if self._is_tty:
            self.stream.write("\033[?1049h")
            self.stream.flush()
        self._started = True

    def render(self, text: str) -> None:
        if not self._started:
            self.start()

        if self._is_tty:
            self.stream.write("\033[H\033[J")
        self.stream.write(text)
        self.stream.write("\n")
        self.stream.flush()

    def stop(self) -> None:
        if not self._started:
            return
        if self._is_tty:
            self.stream.write("\033[?1049l")
            self.stream.flush()
        self._started = False


def _render_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    lines = [
        "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)),
        "  ".join("-" * widths[index] for index in range(len(headers))),
    ]
    for row in rows:
        lines.append("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))
    return "\n".join(lines)


def _format_rate(value: str | None) -> str:
    if value is None or value == "":
        return "-"
    try:
        number = float(value)
    except ValueError:
        return value
    prefix = "+" if number > 0 else ""
    return f"{prefix}{number:.2f}%"
