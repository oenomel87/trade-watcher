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
    engine_port = int(os.getenv("WATCHER_ENGINE_PORT", "9944"))

    if not app_key:
        raise ValueError("KIS_APP_KEY 환경 변수가 설정되지 않았습니다.")
    if not app_secret:
        raise ValueError("KIS_APP_SECRET 환경 변수가 설정되지 않았습니다.")

    return KISConfig(
        app_key=app_key,
        app_secret=app_secret,
        is_real=is_real,
        engine_port=engine_port,
    )
