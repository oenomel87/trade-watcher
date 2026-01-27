"""
인증 모듈

한국투자증권 API 접근 토큰 발급 및 관리를 담당합니다.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx

from db import Database


@dataclass
class TokenInfo:
    """토큰 정보"""

    access_token: str
    token_type: str
    expires_in: int
    expired_at: datetime

    @property
    def is_expired(self) -> bool:
        """토큰 만료 여부 확인 (30분 버퍼)"""
        buffer = timedelta(minutes=30)
        return datetime.now() >= (self.expired_at - buffer)


class TokenManager:
    """
    한국투자증권 API 토큰 관리자

    토큰 발급, 캐싱, 자동 갱신을 담당합니다.
    """

    TOKEN_ENDPOINT = "/oauth2/tokenP"

    def __init__(self, app_key: str, app_secret: str, base_url: str):
        """
        Args:
            app_key: 한국투자증권 앱키
            app_secret: 한국투자증권 앱시크릿
            base_url: API 기본 URL
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self._token_info: TokenInfo | None = None
        self._storage = Database()

    async def get_token(self) -> str:
        """
        접근 토큰 반환

        캐싱된 토큰이 유효하면 반환, 아니면 새로 발급합니다.

        Returns:
            str: 접근 토큰

        Raises:
            TokenError: 토큰 발급 실패 시
        """
        if self._token_info is None:
            self._token_info = self._load_token_from_storage()

        if self._token_info is None or self._token_info.is_expired:
            await self._refresh_token()

        return self._token_info.access_token

    async def _refresh_token(self) -> None:
        """토큰 새로 발급"""
        url = f"{self.base_url}{self.TOKEN_ENDPOINT}"

        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                result = response.json()
        except httpx.RequestError as e:
            raise TokenError(f"토큰 발급 요청 실패: {e}") from e
        except httpx.HTTPStatusError as e:
            raise TokenError(f"토큰 발급 실패: {e.response.status_code}") from e

        # 응답 검증
        if "access_token" not in result:
            error_msg = result.get("error_description", "알 수 없는 에러")
            raise TokenError(f"토큰 발급 실패: {error_msg}")

        # 만료 시간 파싱
        expired_str = result.get("access_token_token_expired", "")
        try:
            expired_at = datetime.strptime(expired_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # 파싱 실패 시 expires_in 사용
            expires_in = result.get("expires_in", 86400)
            expired_at = datetime.now() + timedelta(seconds=expires_in)

        self._token_info = TokenInfo(
            access_token=result["access_token"],
            token_type=result.get("token_type", "Bearer"),
            expires_in=result.get("expires_in", 86400),
            expired_at=expired_at,
        )
        self._save_token_to_storage(self._token_info)

    def _load_token_from_storage(self) -> TokenInfo | None:
        """저장된 토큰을 조회하여 TokenInfo로 복원."""
        try:
            self._storage.create_tables()
            stored = self._storage.get_kis_token(self.app_key, self.base_url)
        except Exception:
            return None

        if not stored or not stored.get("access_token"):
            return None

        expired_at = None
        expired_str = stored.get("expired_at")
        if expired_str:
            try:
                expired_at = datetime.strptime(expired_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                expired_at = None

        if expired_at is None and stored.get("expires_in"):
            expired_at = datetime.now() + timedelta(seconds=stored["expires_in"])

        if expired_at is None:
            return None

        return TokenInfo(
            access_token=stored["access_token"],
            token_type=stored.get("token_type") or "Bearer",
            expires_in=stored.get("expires_in") or 0,
            expired_at=expired_at,
        )

    def _save_token_to_storage(self, token_info: TokenInfo) -> None:
        """발급된 토큰을 저장."""
        try:
            self._storage.create_tables()
            self._storage.upsert_kis_token(
                app_key=self.app_key,
                base_url=self.base_url,
                access_token=token_info.access_token,
                token_type=token_info.token_type,
                expires_in=token_info.expires_in,
                expired_at=token_info.expired_at.strftime("%Y-%m-%d %H:%M:%S"),
            )
        except Exception:
            # 저장 실패는 토큰 발급 흐름을 막지 않음
            pass

    def get_token_info(self) -> TokenInfo | None:
        """현재 토큰 정보 반환"""
        return self._token_info

    def invalidate(self) -> None:
        """캐싱된 토큰 무효화"""
        self._token_info = None
        try:
            self._storage.delete_kis_token(self.app_key, self.base_url)
        except Exception:
            pass


class TokenError(Exception):
    """토큰 관련 에러"""

    pass
