"""Watch list 서비스 샘플 테스트."""

from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.watchlist_service import WatchListService  # noqa: E402
from db import Database  # noqa: E402


def test_watchlist_flow():
    db = Database(":memory:")
    service = WatchListService(db=db)

    watchlist = service.create_watchlist("관심종목", "장기투자")
    assert watchlist["name"] == "관심종목"
    assert watchlist["default_folder"]["is_default"] is True

    folders = service.list_folders(watchlist["id"])
    assert len(folders) == 1

    folder = service.create_folder(watchlist["id"], "반도체", "메모리")
    assert folder["name"] == "반도체"

    item = service.add_item(watchlist["id"], "005930", folder_id=folder["id"], memo="삼성전자")
    assert item["stock_code"] == "005930"

    items = service.list_items(watchlist["id"], folder_id=folder["id"])
    assert len(items) == 1

    root_item = service.add_item(watchlist["id"], "000660", memo="SK하이닉스")
    assert root_item["folder_id"] is None

    service.delete_item(watchlist["id"], items[0]["id"])
    items = service.list_items(watchlist["id"], folder_id=folder["id"])
    assert len(items) == 0


@pytest.mark.asyncio
async def test_watchlist_summary_cache():
    db = Database(":memory:")
    service = WatchListService(db=db)
    watchlist = service.create_watchlist("관심종목", "요약 테스트")

    service.add_item(watchlist["id"], "005930", memo="삼성전자")
    db.upsert_current_price(
        stock_code="005930",
        market="J",
        price_json='{"stck_prpr":"71000","acml_vol":"1000","prdy_vrss":"500","prdy_ctrt":"0.70"}',
    )

    items = await service.list_items_with_price(
        watchlist_id=watchlist["id"],
        use_cache=True,
        refresh_missing=False,
        market="J",
    )

    assert len(items) == 1
    assert items[0]["current_price"] == "71000"
    assert items[0]["volume"] == "1000"
    assert items[0]["change"] == "500"

