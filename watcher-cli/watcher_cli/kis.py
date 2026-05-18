from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Any

import httpx

from watcher_cli.config import KISConfig, load_config

RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class APIError(Exception):
    def __init__(self, message: str, response: dict[str, Any] | None = None):
        super().__init__(message)
        self.response = response


def is_retryable_request_error(exc: httpx.RequestError) -> bool:
    return not isinstance(exc, (httpx.ReadTimeout, httpx.WriteTimeout))


@dataclass
class TokenInfo:
    access_token: str
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        return datetime.now() >= (self.expires_at - timedelta(minutes=30))


class TokenManager:
    TOKEN_ENDPOINT = "/oauth2/tokenP"

    def __init__(self, config: KISConfig, cache_path: Path | None = None):
        self.config = config
        self._token_info: TokenInfo | None = None
        self._lock = asyncio.Lock()
        self.cache_path = cache_path or (
            Path.home() / ".config" / "trade-watcher" / "kis_token.json"
        )

    async def get_token(self) -> str:
        async with self._lock:
            if self._token_info is None:
                self._token_info = self._load_token()
            if self._token_info is None or self._token_info.is_expired:
                self._token_info = await self._fetch_token()
                self._save_token(self._token_info)
            return self._token_info.access_token

    async def _fetch_token(self) -> TokenInfo:
        url = f"{self.config.base_url}{self.TOKEN_ENDPOINT}"
        data = {
            "grant_type": "client_credentials",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
        }

        attempt = 0
        while True:
            try:
                async with httpx.AsyncClient(timeout=self.config.timeout_sec) as client:
                    response = await client.post(url, json=data)
                    response.raise_for_status()
                    payload = response.json()
                break
            except httpx.RequestError as exc:
                if attempt >= self.config.max_retries or not is_retryable_request_error(exc):
                    raise APIError(f"토큰 발급 요청 실패: {exc}") from exc
            except httpx.HTTPStatusError as exc:
                if attempt >= self.config.max_retries or exc.response.status_code not in RETRY_STATUS_CODES:
                    raise APIError(f"토큰 발급 실패: {exc.response.status_code}") from exc
            await asyncio.sleep(self.config.retry_backoff_sec * (2**attempt))
            attempt += 1

        token = payload.get("access_token")
        if not token:
            raise APIError("토큰 발급 실패", response=payload)

        expired_str = payload.get("access_token_token_expired")
        if expired_str:
            try:
                expires_at = datetime.strptime(expired_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                expires_at = datetime.now() + timedelta(seconds=payload.get("expires_in", 86400))
        else:
            expires_at = datetime.now() + timedelta(seconds=payload.get("expires_in", 86400))

        return TokenInfo(access_token=token, expires_at=expires_at)

    def _load_token(self) -> TokenInfo | None:
        if not self.cache_path.exists():
            return None
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        access_token = payload.get("access_token")
        expired_at = payload.get("expired_at")
        if not access_token or not expired_at:
            return None

        try:
            expires_at = datetime.strptime(expired_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

        return TokenInfo(access_token=access_token, expires_at=expires_at)

    def _save_token(self, token_info: TokenInfo) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "access_token": token_info.access_token,
            "expired_at": token_info.expires_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.cache_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


class KISClient:
    def __init__(self, config: KISConfig | None = None, client: httpx.AsyncClient | None = None):
        self.config = config or load_config()
        self.token_manager = TokenManager(self.config)
        self._client = client or httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout_sec,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> KISClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def get_current_price(self, stock_code: str, market: str = "J") -> dict[str, Any]:
        return await self._get(
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "fid_cond_mrkt_div_code": market,
                "fid_input_iscd": stock_code,
            },
            extra_headers={"custtype": "P"},
        )

    async def get_overseas_price(self, exchange: str, symbol: str) -> dict[str, Any]:
        return await self._get(
            "/uapi/overseas-price/v1/quotations/price-detail",
            tr_id="HHDFS76200200",
            params={
                "AUTH": "",
                "EXCD": exchange,
                "SYMB": symbol,
            },
            extra_headers={"custtype": "P"},
        )

    async def _get(
        self,
        endpoint: str,
        tr_id: str,
        params: dict[str, Any],
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        headers = await self._build_headers(tr_id)
        if extra_headers:
            headers.update(extra_headers)

        response = await self._client.get(endpoint, headers=headers, params=params)
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw_response": response.text}

        if not response.is_success:
            raise APIError(f"API 요청 실패: {response.status_code}", response=payload)
        return payload

    async def _build_headers(self, tr_id: str) -> dict[str, str]:
        token = await self.token_manager.get_token()
        return {
            "authorization": f"Bearer {token}",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
            "tr_id": tr_id,
            "content-type": "application/json; charset=utf-8",
        }
