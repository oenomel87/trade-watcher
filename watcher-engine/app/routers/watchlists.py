"""Watch list API 라우터."""

from fastapi import APIRouter, HTTPException, Query

from app.services.watchlist_service import WatchListService


router = APIRouter()


@router.get("")
async def list_watchlists():
    """Watch list 목록 조회."""
    service = WatchListService()
    watchlists = service.list_watchlists()
    return {"watchlists": watchlists, "count": len(watchlists)}


@router.post("")
async def create_watchlist(
    name: str = Query(..., min_length=1, description="watch list 이름"),
    description: str | None = Query(None, description="설명"),
):
    """Watch list 생성 (기본 폴더 포함)."""
    service = WatchListService()
    try:
        return service.create_watchlist(name=name, description=description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{watchlist_id}")
async def get_watchlist(
    watchlist_id: int,
    include_folders: bool = Query(True, description="폴더 포함 여부"),
    include_items: bool = Query(False, description="종목 포함 여부"),
):
    """Watch list 상세 조회."""
    service = WatchListService()
    watchlist = service.get_watchlist(watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="watch list를 찾을 수 없습니다.")

    if include_folders:
        folders = service.list_folders(watchlist_id)
        watchlist["folders"] = folders
        if include_items:
            items = service.list_items(watchlist_id)
            watchlist["items"] = items

    return watchlist


@router.delete("/{watchlist_id}")
async def delete_watchlist(watchlist_id: int):
    """Watch list 삭제."""
    service = WatchListService()
    service.delete_watchlist(watchlist_id)
    return {"message": "watch list 삭제 완료"}


@router.get("/{watchlist_id}/folders")
async def list_folders(watchlist_id: int):
    """폴더 목록 조회."""
    service = WatchListService()
    folders = service.list_folders(watchlist_id)
    return {"folders": folders, "count": len(folders)}


@router.post("/{watchlist_id}/folders")
async def create_folder(
    watchlist_id: int,
    name: str = Query(..., min_length=1, description="폴더 이름"),
    description: str | None = Query(None, description="설명"),
):
    """폴더 생성."""
    service = WatchListService()
    try:
        return service.create_folder(watchlist_id, name, description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{watchlist_id}/folders/{folder_id}")
async def update_folder(
    watchlist_id: int,
    folder_id: int,
    name: str | None = Query(None, description="폴더 이름"),
    description: str | None = Query(None, description="설명"),
):
    """폴더 수정."""
    service = WatchListService()
    try:
        result = service.update_folder(watchlist_id, folder_id, name, description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not result:
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")

    return result


@router.delete("/{watchlist_id}/folders/{folder_id}")
async def delete_folder(watchlist_id: int, folder_id: int):
    """폴더 삭제."""
    service = WatchListService()
    try:
        service.delete_folder(watchlist_id, folder_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "폴더 삭제 완료"}


@router.get("/{watchlist_id}/items")
async def list_items(
    watchlist_id: int,
    folder_id: int | None = Query(None, description="폴더 ID"),
):
    """watch list 종목 목록 조회."""
    service = WatchListService()
    items = service.list_items(watchlist_id, folder_id)
    return {"items": items, "count": len(items)}


@router.post("/{watchlist_id}/items")
async def add_item(
    watchlist_id: int,
    stock_code: str = Query(..., min_length=1, description="종목 코드"),
    folder_id: int | None = Query(None, description="폴더 ID (없으면 최상위)"),
    memo: str | None = Query(None, description="메모"),
):
    """watch list 종목 추가."""
    service = WatchListService()
    try:
        return service.add_item(watchlist_id, stock_code, folder_id, memo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{watchlist_id}/items/summary")
async def list_items_summary(
    watchlist_id: int,
    folder_id: int | None = Query(None, description="폴더 ID"),
    use_cache: bool = Query(True, description="DB 캐시 사용 여부"),
    max_age_sec: int | None = Query(None, ge=0, description="캐시 허용 최대 경과초"),
    refresh_missing: bool = Query(False, description="캐시 누락 시 실시간 조회"),
    market: str = Query("J", description="시장 구분 (J/NX/UN)"),
):
    """watch list 종목 + 현재가 요약 조회."""
    service = WatchListService()
    try:
        items = service.list_items_with_price(
            watchlist_id=watchlist_id,
            folder_id=folder_id,
            use_cache=use_cache,
            max_age_sec=max_age_sec,
            refresh_missing=refresh_missing,
            market=market,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"items": items, "count": len(items)}


@router.delete("/{watchlist_id}/items/{item_id}")
async def delete_item(watchlist_id: int, item_id: int):
    """watch list 종목 삭제."""
    service = WatchListService()
    service.delete_item(watchlist_id, item_id)
    return {"message": "종목 삭제 완료"}
