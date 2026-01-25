"""Configuration loader for the CLI."""

from __future__ import annotations

from pathlib import Path
import json
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CliConfig(BaseModel):
    """Top-level CLI settings."""

    engine_url: str = Field(default="http://localhost:8000")
    refresh_interval_sec: int = Field(default=2, ge=1)
    summary_cache_age_sec: int = Field(default=60, ge=0)
    market: str = Field(default="J")
    default_watchlist_id: int | None = None
    model_config = ConfigDict(extra="ignore")


def resolve_config_path(config_path: str | Path | None = None) -> Path | None:
    """Resolve the first available config path using the search order."""
    if config_path is not None:
        path = Path(config_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        return path

    for candidate in _config_search_paths():
        if candidate.exists():
            return candidate

    return None


def load_config(config_path: str | Path | None = None) -> CliConfig:
    """Load config from file (if any) and apply environment overrides."""
    data: dict[str, Any] = {}
    path = resolve_config_path(config_path)
    if path is not None:
        data = _read_json(path)

    config = CliConfig.model_validate(data)
    return _apply_env_overrides(config)


def _config_search_paths() -> list[Path]:
    module_root = Path(__file__).resolve().parents[1]
    paths = [
        module_root / "cli_config.json",
        module_root / "tui_config.json",
    ]

    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_home:
        paths.append(Path(xdg_home) / "trade-watcher" / "cli_config.json")
        paths.append(Path(xdg_home) / "trade-watcher" / "tui_config.json")

    paths.append(Path.home() / ".config" / "trade-watcher" / "cli_config.json")
    paths.append(Path.home() / ".config" / "trade-watcher" / "tui_config.json")
    return paths


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config file: {path}") from exc


def _apply_env_overrides(config: CliConfig) -> CliConfig:
    data = config.model_dump()
    env = os.environ

    _set_if_present(data, "engine_url", env.get("WATCHER_ENGINE_URL"))
    _set_if_present(
        data,
        "refresh_interval_sec",
        _parse_int(env.get("WATCHER_CLI_REFRESH_SEC") or env.get("WATCHER_TUI_REFRESH_SEC")),
    )
    _set_if_present(
        data,
        "summary_cache_age_sec",
        _parse_int(env.get("WATCHER_CLI_SUMMARY_CACHE_SEC") or env.get("WATCHER_TUI_SUMMARY_CACHE_SEC")),
    )
    _set_if_present(
        data,
        "market",
        env.get("WATCHER_CLI_MARKET") or env.get("WATCHER_TUI_MARKET"),
    )
    _set_if_present(
        data,
        "default_watchlist_id",
        _parse_int(env.get("WATCHER_CLI_DEFAULT_WATCHLIST_ID") or env.get("WATCHER_TUI_DEFAULT_WATCHLIST_ID")),
    )
    return CliConfig.model_validate(data)


def _set_if_present(container: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        container[key] = value


def _parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid integer value: {value}") from None
