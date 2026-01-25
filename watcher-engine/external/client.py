"""
HTTP API 클라이언트 기본 모듈

다양한 API 연동을 위한 공통 HTTP 클라이언트를 제공합니다.
"""

from typing import Any

import requests
from requests.exceptions import RequestException


class APIError(Exception):
    """API 에러"""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class BaseAPIClient:
    """
    HTTP API 클라이언트 기본 클래스

    모든 API 클라이언트가 상속받아 사용합니다.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Args:
            base_url: API 기본 URL
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _build_url(self, endpoint: str) -> str:
        """전체 URL 생성"""
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _request(
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
        url = self._build_url(endpoint)
        default_headers = {"Content-Type": "application/json"}

        if headers:
            default_headers.update(headers)

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=default_headers,
                params=params,
                json=json_data,
                timeout=self.timeout,
            )

            # 응답 JSON 파싱
            try:
                result = response.json()
            except ValueError:
                result = {"raw_response": response.text}

            # HTTP 에러 확인
            if not response.ok:
                raise APIError(
                    message=f"API 요청 실패: {response.status_code}",
                    status_code=response.status_code,
                    response=result,
                )

            return result

        except RequestException as e:
            raise APIError(f"네트워크 에러: {e}") from e

    def get(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """GET 요청"""
        return self._request("GET", endpoint, headers=headers, params=params)

    def post(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """POST 요청"""
        return self._request("POST", endpoint, headers=headers, json_data=json_data)

    def close(self) -> None:
        """세션 종료"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
