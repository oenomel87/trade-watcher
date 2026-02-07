"""
HTTP API 클라이언트 기본 모듈

다양한 API 연동을 위한 공통 HTTP 클라이언트를 제공합니다.
"""

import asyncio
from typing import Any

import httpx

RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504}


def is_retryable_request_error(exc: httpx.RequestError) -> bool:
    """재시도 가능한 네트워크 오류인지 판단."""
    return not isinstance(exc, (httpx.ReadTimeout, httpx.WriteTimeout))


class APIError(Exception):
    """API 에러"""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class BaseAPIClient:
    """
    비동기 HTTP API 클라이언트 기본 클래스

    모든 API 클라이언트가 상속받아 사용합니다.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_concurrency: int | None = None,
        max_retries: int = 0,
        retry_backoff_sec: float = 0.0,
    ):
        """
        Args:
            base_url: API 기본 URL
            timeout: 요청 타임아웃 (초)
            max_concurrency: 동시 호출 제한 (None이면 제한 없음)
            max_retries: 요청 재시도 횟수
            retry_backoff_sec: 재시도 기본 대기 시간(초)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrency) if max_concurrency else None
        self.max_retries = max_retries
        self.retry_backoff_sec = retry_backoff_sec
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """클라이언트 인스턴스 반환 (lazy initialization)"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    def _build_url(self, endpoint: str) -> str:
        """전체 URL 생성"""
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        HTTP 요청 실행

        Args:
            method: HTTP 메서드 (GET, POST, etc.)
            endpoint: API 엔드포인트
            headers: 요청 헤더
            params: 쿼리 파라미터
            json_data: JSON 요청 본문

        Returns:
            dict: JSON 응답

        Raises:
            APIError: API 요청 실패 시
        """
        client = await self._get_client()
        url = endpoint.lstrip("/")
        default_headers = {"Content-Type": "application/json"}

        if headers:
            default_headers.update(headers)

        attempt = 0
        while True:
            try:
                if self._semaphore is None:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=default_headers,
                        params=params,
                        json=json_data,
                    )
                else:
                    async with self._semaphore:
                        response = await client.request(
                            method=method,
                            url=url,
                            headers=default_headers,
                            params=params,
                            json=json_data,
                        )
            except httpx.RequestError as exc:
                if attempt >= self.max_retries or not is_retryable_request_error(exc):
                    raise APIError(f"네트워크 에러: {exc}") from exc
                await self._sleep_backoff(attempt)
                attempt += 1
                continue

            if response.is_success:
                return self._parse_response(response)

            if response.status_code in RETRY_STATUS_CODES and attempt < self.max_retries:
                await self._sleep_backoff(attempt, response)
                attempt += 1
                continue

            result = self._parse_response(response)
            raise APIError(
                message=f"API 요청 실패: {response.status_code}",
                status_code=response.status_code,
                response=result,
            )

    async def get(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """GET 요청"""
        return await self._request("GET", endpoint, headers=headers, params=params)

    async def post(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """POST 요청"""
        return await self._request("POST", endpoint, headers=headers, json_data=json_data)

    async def close(self) -> None:
        """클라이언트 종료"""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _parse_response(self, response: httpx.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            return {"raw_response": response.text}

    async def _sleep_backoff(self, attempt: int, response: httpx.Response | None = None) -> None:
        delay = self.retry_backoff_sec * (2**attempt)
        if response is not None:
            retry_after = response.headers.get("retry-after")
            if retry_after:
                try:
                    retry_after_sec = float(retry_after)
                    delay = max(delay, retry_after_sec)
                except ValueError:
                    pass
        if delay > 0:
            await asyncio.sleep(delay)
