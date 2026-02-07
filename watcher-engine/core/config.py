"""
애플리케이션 설정 모듈

환경 변수에서 설정값을 로드하고 관리합니다.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class KISConfig:
    """한국투자증권 API 설정"""

    app_key: str
    app_secret: str
    is_real: bool = False  # True: 실전, False: 모의
    engine_port: int = 9944  # 엔진 실행 포트
    kis_max_concurrency: int = 5  # KIS 동시 호출 제한
    kis_timeout_sec: float = 30.0  # KIS 요청 타임아웃 (초)
    kis_max_retries: int = 2  # KIS 재시도 횟수
    kis_retry_backoff_sec: float = 0.5  # 재시도 백오프 기본값 (초)

    @property
    def base_url(self) -> str:
        """환경에 따른 기본 URL 반환"""
        if self.is_real:
            return "https://openapi.koreainvestment.com:9443"
        return "https://openapivts.koreainvestment.com:29443"


def load_config() -> KISConfig:
    """
    환경 변수에서 설정을 로드합니다.

    Returns:
        KISConfig: 한국투자증권 API 설정 객체

    Raises:
        ValueError: 필수 환경 변수가 없을 경우
    """
    # .env 파일 로드 (프로젝트 루트 우선)
    base_dir = Path(__file__).resolve().parent
    env_candidates = [
        base_dir.parent / ".env",
        base_dir / ".env",
    ]
    for env_path in env_candidates:
        if env_path.exists():
            load_dotenv(env_path)
            break

    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    is_real = os.getenv("KIS_IS_REAL", "false").lower() == "true"
    engine_port = _get_env_int("WATCHER_ENGINE_PORT", 9944, min_value=1)
    kis_max_concurrency = _get_env_int("WATCHER_KIS_MAX_CONCURRENCY", 5, min_value=1)
    kis_timeout_sec = _get_env_float("WATCHER_KIS_TIMEOUT_SEC", 30.0, min_value=0.1)
    kis_max_retries = _get_env_int("WATCHER_KIS_MAX_RETRIES", 2, min_value=0)
    kis_retry_backoff_sec = _get_env_float("WATCHER_KIS_RETRY_BACKOFF_SEC", 0.5, min_value=0.0)

    if not app_key:
        raise ValueError("KIS_APP_KEY 환경 변수가 설정되지 않았습니다.")
    if not app_secret:
        raise ValueError("KIS_APP_SECRET 환경 변수가 설정되지 않았습니다.")

    return KISConfig(
        app_key=app_key,
        app_secret=app_secret,
        is_real=is_real,
        engine_port=engine_port,
        kis_max_concurrency=kis_max_concurrency,
        kis_timeout_sec=kis_timeout_sec,
        kis_max_retries=kis_max_retries,
        kis_retry_backoff_sec=kis_retry_backoff_sec,
    )


def _get_env_int(name: str, default: int, min_value: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name}는 정수여야 합니다.") from exc
    if min_value is not None and value < min_value:
        raise ValueError(f"{name}는 {min_value} 이상이어야 합니다.")
    return value


def _get_env_float(name: str, default: float, min_value: float | None = None) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name}는 숫자여야 합니다.") from exc
    if min_value is not None and value < min_value:
        raise ValueError(f"{name}는 {min_value} 이상이어야 합니다.")
    return value
