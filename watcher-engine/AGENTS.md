# Repository Guidelines

## Project Structure & Module Organization
- `app/`: FastAPI entrypoint and routers (`app/main.py`, `app/routers/`), plus service layer in `app/services/`.
- `core/`: shared configuration helpers (`core/config.py`) and env loading.
- `external/`: API clients and auth for Korea Investment & Securities (`external/kis/`).
- `db/`: SQLite connection + models.
- `loaders/`: data ingestion utilities (e.g., `loaders/stock_parser.py`).
- `data/`: local SQLite storage (`data/stocks.db`).

## Build, Test, and Development Commands
- `uv sync`: install dependencies into the uv-managed environment.
- `uv run uvicorn app.main:app --reload`: run the API server with hot reload.
- `uv run python -m loaders.stock_parser ...`: run loader scripts when adding data (adjust args as needed).

## Coding Style & Naming Conventions
- Language: Python 3.13+.
- Indentation: 4 spaces; follow PEP 8 conventions.
- Modules: snake_case filenames; classes in `CamelCase`; functions in `snake_case`.
- No formatter or linter is configured yet; keep imports tidy and avoid unused symbols.

## Testing Guidelines
- No test framework is configured in this repo yet.
- When adding tests, place them in `tests/` and name files `test_*.py`.
- Use `uv run pytest` once a test suite is introduced.

## Commit & Pull Request Guidelines
- No commit history exists yet, so no established convention.
- Suggested baseline: short, imperative commit subjects (e.g., “Add stock search endpoint”).
- PRs should include: a clear summary, linked issue (if any), and API/behavior notes.

## Security & Configuration Tips
- Store KIS credentials in `.env` (`KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_IS_REAL`).
- Never commit real API keys or the `data/stocks.db` file if it contains sensitive data.
