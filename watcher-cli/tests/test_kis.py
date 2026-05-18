from datetime import datetime, timedelta
from pathlib import Path

import pytest

from watcher_cli.config import KISConfig
from watcher_cli.kis import TokenInfo, TokenManager


@pytest.mark.asyncio
async def test_token_manager_reuses_persisted_token(tmp_path: Path):
    config = KISConfig(
        app_key="key",
        app_secret="secret",
        is_real=True,
    )
    cache_path = tmp_path / "token.json"
    token_info = TokenInfo(
        access_token="persisted-token",
        expires_at=datetime.now() + timedelta(hours=1),
    )

    manager = TokenManager(config, cache_path=cache_path)
    manager._save_token(token_info)

    called = False

    async def unexpected_fetch():
        nonlocal called
        called = True
        return token_info

    manager._fetch_token = unexpected_fetch  # type: ignore[method-assign]

    token = await manager.get_token()

    assert token == "persisted-token"
    assert called is False
