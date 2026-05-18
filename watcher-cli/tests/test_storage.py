from pathlib import Path

from watcher_cli.models import WatchItem
from watcher_cli.storage import JsonWatchlistStorage


def test_storage_add_list_remove(tmp_path: Path):
    storage = JsonWatchlistStorage(tmp_path / "watchlist.json")

    samsung = WatchItem(symbol="005930", name="삼성전자", market="KR")
    apple = WatchItem(
        symbol="AAPL",
        name="Apple",
        market="US",
        exchange="NAS",
        aliases=("애플",),
    )

    storage.add(samsung)
    storage.add(apple)
    storage.add(samsung)

    items = storage.list_items()
    assert items == [samsung, apple]

    removed = storage.remove("005930")
    assert removed == samsung
    assert storage.list_items() == [apple]

    removed_apple = storage.remove("애플")
    assert removed_apple == apple
    assert storage.list_items() == []
