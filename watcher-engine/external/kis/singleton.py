"""전역 KISClient 인스턴스 제공.

앱 전체에서 하나의 KISClient 인스턴스를 재사용하여
토큰 관리 효율성을 높입니다.
"""

from external.kis.client import KISClient
from core.config import load_config

_client: KISClient | None = None


def get_kis_client() -> KISClient:
    """KISClient 싱글톤 인스턴스 반환.

    Returns:
        KISClient: 전역 KIS API 클라이언트
    """
    global _client
    if _client is None:
        _client = KISClient(load_config())
    return _client


def reset_kis_client() -> None:
    """테스트용: 클라이언트 인스턴스 초기화."""
    global _client
    _client = None
