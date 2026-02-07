# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trade Watcher is a real-time stock monitoring and watchlist management system using the Korea Investment & Securities (KIS) API. It consists of two independent Python packages that communicate via HTTP.

## Build and Development Commands

All packages use [uv](https://docs.astral.sh/uv/) for dependency management. Run commands from each subproject directory.

### watcher-engine (Backend)
```bash
cd watcher-engine
uv sync                                          # Install dependencies
uv run python -m app.main                        # Start server (default: http://localhost:9944)
uv run uvicorn app.main:app --reload             # Start with hot reload
uv run pytest                                    # Run all tests
uv run pytest tests/test_current_price.py       # Run single test file
uv run python -m loaders.stock_parser <args>    # Ingest stock data
```

### watcher-cli (Frontend)
```bash
cd watcher-cli
uv sync                                          # Install dependencies
uv run python main.py watchlists                 # List watchlists
uv run python main.py items --watchlist 1 -w    # Monitor watchlist in real-time
```

## Architecture

### watcher-engine
FastAPI backend with a layered architecture:

- **app/main.py**: Application entrypoint, FastAPI app with lifespan for DB initialization
- **app/routers/**: API route handlers (`stocks.py`, `watchlists.py`)
- **app/services/**: Business logic layer - each service handles a specific domain (stock prices, watchlists, etc.)
- **external/kis/client.py**: KIS API client with automatic token management via `TokenManager`
- **external/auth.py**: OAuth token lifecycle management for KIS API
- **db/**: SQLite database layer with dataclass models
- **loaders/stock_parser.py**: Data ingestion for KOSPI/KOSDAQ/US stock master data

The engine supports multiple exchanges: KRX (main Korean exchange), NXT (alternative Korean exchange), and US markets.

### watcher-cli
Async CLI client using argparse and httpx:

- **main.py**: Command parser and async command handlers
- **watcher_cli/client.py**: HTTP client for communicating with watcher-engine
- **watcher_cli/models.py**: Pydantic models for API responses
- **watcher_cli/config.py**: Configuration loading from files and environment variables

The CLI supports both one-shot commands and continuous watch mode (`-w` flag) with terminal-based refresh.

## Environment Configuration

### watcher-engine/.env
```env
KIS_APP_KEY=<your_app_key>
KIS_APP_SECRET=<your_app_secret>
KIS_IS_REAL=false              # true for production, false for sandbox
WATCHER_ENGINE_PORT=9944       # Optional, defaults to 9944
```

### watcher-cli configuration
Config file search order: `watcher-cli/cli_config.json` > `~/.config/trade-watcher/cli_config.json`

Environment variables: `WATCHER_ENGINE_URL`, `WATCHER_CLI_REFRESH_SEC`, `WATCHER_CLI_DEFAULT_WATCHLIST_ID`

## Coding Conventions

- Python 3.13+, PEP 8 style, 4-space indentation
- snake_case for files/functions, CamelCase for classes
- Tests in `watcher-engine/tests/` named `test_*.py`
- Use pytest with pytest-asyncio for async tests
- Test pattern: Create fake clients (e.g., `FakeKISClient`) as test doubles

## Key Data Models

- **Stock**: code, standard_code, name, market (KOSPI/KOSDAQ/US), exchange (KRX/NXT/US)
- **StockListing**: Maps stocks to exchanges, tracks primary exchange
- **Watchlist**: User-defined stock collections with folders

## API Market Codes

- Stock filtering: `KOSPI`, `KOSDAQ`, `US`
- Price queries: `J` (KRX main), `NX` (NXT), `UN` (US)
