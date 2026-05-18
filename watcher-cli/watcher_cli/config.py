from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class KISConfig:
    app_key: str
    app_secret: str
    is_real: bool = False
    timeout_sec: float = 30.0
    max_retries: int = 2
    retry_backoff_sec: float = 0.5

    @property
    def base_url(self) -> str:
        if self.is_real:
            return "https://openapi.koreainvestment.com:9443"
        return "https://openapivts.koreainvestment.com:29443"


def load_config() -> KISConfig:
    for env_path in _env_candidates():
        if env_path.exists():
            load_dotenv(env_path, override=False)
            break

    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    is_real = os.getenv("KIS_IS_REAL", "false").lower() == "true"
    if not app_key:
        raise ValueError("KIS_APP_KEY 환경 변수가 설정되지 않았습니다.")
    if not app_secret:
        raise ValueError("KIS_APP_SECRET 환경 변수가 설정되지 않았습니다.")
    return KISConfig(
        app_key=app_key,
        app_secret=app_secret,
        is_real=is_real,
    )


def _env_candidates() -> list[Path]:
    project_root = Path(__file__).resolve().parents[1]
    return [
        Path.cwd() / ".env",
        project_root / ".env",
    ]
