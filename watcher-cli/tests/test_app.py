import asyncio
import sys

import pytest

from watcher_cli.app import _run_add, _run_monitor, build_parser, main
from watcher_cli.config import load_config
from watcher_cli.catalog import StockCatalog
from watcher_cli.models import CatalogEntry, WatchItem
from watcher_cli.storage import JsonWatchlistStorage


def test_parser_supports_simplified_commands():
    parser = build_parser()

    add_args = parser.parse_args(["add", "삼성전자"])
    monitor_args = parser.parse_args(["monitor", "--interval", "5"])

    assert add_args.command == "add"
    assert add_args.query == "삼성전자"
    assert monitor_args.command == "monitor"
    assert monitor_args.interval == 5


def test_parser_rejects_legacy_watchlist_command():
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["watchlists"])


def test_run_add_reports_duplicate_symbol(tmp_path, monkeypatch, capsys):
    storage = JsonWatchlistStorage(tmp_path / "watchlist.json")
    storage.add(WatchItem(symbol="005930", name="삼성전자", market="KR"))

    monkeypatch.setattr(
        "watcher_cli.app.StockCatalog.from_default_files",
        lambda: StockCatalog.from_entries(
            [CatalogEntry(symbol="005930", name="삼성전자", market="KR", exchange=None)]
        ),
    )

    _run_add(storage, "005930")

    captured = capsys.readouterr()
    assert "이미 저장된 종목입니다." in captured.out


def test_run_add_handles_missing_stdin_for_ambiguous_result(tmp_path, monkeypatch, capsys):
    storage = JsonWatchlistStorage(tmp_path / "watchlist.json")

    monkeypatch.setattr(
        "watcher_cli.app.StockCatalog.from_default_files",
        lambda: StockCatalog.from_entries(
            [
                CatalogEntry(symbol="AAPL", name="Apple", market="US", exchange="NAS"),
                CatalogEntry(symbol="APLE", name="Apple Hospitality", market="US", exchange="NYS"),
            ]
        ),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: (_ for _ in ()).throw(EOFError()))

    _run_add(storage, "App")

    captured = capsys.readouterr()
    assert "취소되었습니다." in captured.out


def test_main_prints_monitor_error_without_traceback(monkeypatch, capsys):
    async def failing_monitor(_storage, _interval):
        raise ValueError("KIS_APP_KEY 환경 변수가 설정되지 않았습니다.")

    monkeypatch.setattr("watcher_cli.app._run_monitor", failing_monitor)
    monkeypatch.setattr(sys, "argv", ["watcher", "monitor"])

    with pytest.raises(SystemExit) as exc:
        main()

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "KIS_APP_KEY 환경 변수가 설정되지 않았습니다." in captured.out


def test_load_config_reads_dotenv_from_project_root(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "KIS_APP_KEY=test-key\nKIS_APP_SECRET=test-secret\nKIS_IS_REAL=true\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("KIS_APP_KEY", raising=False)
    monkeypatch.delenv("KIS_APP_SECRET", raising=False)
    monkeypatch.delenv("KIS_IS_REAL", raising=False)

    config = load_config()

    assert config.app_key == "test-key"
    assert config.app_secret == "test-secret"
    assert config.is_real is True


@pytest.mark.asyncio
async def test_monitor_does_not_require_kis_client_for_empty_watchlist(tmp_path, monkeypatch):
    storage = JsonWatchlistStorage(tmp_path / "watchlist.json")

    class RaisingQuoteService:
        def __init__(self):
            raise AssertionError("QuoteService should not be constructed")

    async def stop_after_first_tick(_interval: float):
        raise RuntimeError("stop")

    monkeypatch.setattr("watcher_cli.app.QuoteService", RaisingQuoteService)
    monkeypatch.setattr("watcher_cli.app.asyncio.sleep", stop_after_first_tick)

    with pytest.raises(RuntimeError, match="stop"):
        await _run_monitor(storage, 5.0)
