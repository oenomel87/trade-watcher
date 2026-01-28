# Repository Guidelines

## Project Structure & Module Organization
- `watcher-engine/`: FastAPI service, data loaders, and persistence.
  - `watcher-engine/app/`: API entrypoint and routers (`app/main.py`, `app/routers/`).
  - `watcher-engine/app/services/`: service layer for stocks and watchlists.
  - `watcher-engine/core/`: shared configuration helpers and env loading.
  - `watcher-engine/external/`: Korea Investment & Securities (KIS) API client and auth.
  - `watcher-engine/db/`: SQLite models and database wiring.
  - `watcher-engine/loaders/`: data ingestion helpers.
  - `watcher-engine/tests/`: pytest suites (e.g., `test_*.py`).
  - `watcher-engine/data/`: local SQLite storage (`data/stocks.db`).
- `watcher-cli/`: CLI package (`main.py`, `pyproject.toml`, `watcher_cli/`).
- `docs/`: API notes, stock lists, and reference spreadsheets.

## Build, Test, and Development Commands
Run commands from the relevant subproject directory.
- `cd watcher-engine && uv sync`: install dependencies using uv.
- `cd watcher-engine && uv run uvicorn app.main:app --reload`: start the API server with hot reload.
- `cd watcher-engine && uv run pytest`: run tests in `watcher-engine/tests/`.
- `cd watcher-engine && uv run python -m loaders.stock_parser <args>`: ingest stock data (adjust arguments per loader).
- `cd watcher-cli && uv sync`: install CLI dependencies using uv.
- `cd watcher-cli && uv run python main.py watchlists`: run the CLI (example command).

## Coding Style & Naming Conventions
- Language: Python 3.13+.
- Indentation: 4 spaces; follow PEP 8 conventions.
- Naming: `snake_case` for files/functions, `CamelCase` for classes, `UPPER_SNAKE_CASE` for constants.
- No formatter or linter is configured yet; keep imports minimal and avoid unused symbols.

## Testing Guidelines
- Framework: pytest (declared in `watcher-engine/pyproject.toml`).
- Place new tests in `watcher-engine/tests/` and name them `test_*.py`.
- Prefer unit tests for service-layer logic and integration tests for external API boundaries.

## Commit & Pull Request Guidelines
- There is no commit history yet, so no established convention.
- Suggested baseline: short, imperative commit subjects (example: "Add watchlist summary endpoint").
- PRs should include: a concise summary, linked issue (if any), and notes on API or schema changes.

## Security & Configuration Tips
- Store KIS credentials in a local `.env` file inside `watcher-engine/`:
  `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_IS_REAL`.
- Do not commit real API keys or local SQLite data (`watcher-engine/data/stocks.db`).
