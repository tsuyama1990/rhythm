# rhythm

*beat the rhythm of stock trend*

## Overview
A Japanese Stock Calendar Anomaly Analysis System utilizing J-Quants API for data ingestion, Polars for ETL processing, DuckDB for EDA, and vectorbt for backtesting.

## Architecture & Guidelines
- Core logic strictly separated into `src/` directory.
- Execution and exploratory analysis restricted to `notebooks/` directory.
- Processed ETL data should be saved locally in Parquet format to optimize storage and I/O performance.
- **Strict Look-Ahead Bias Prevention:** All trading signal logic must use `shift(1)` to reference only the previous day's data.

## Environment & Setup
- Target development environment is WSL2 (Ubuntu) on Windows.
- The project uses `uv` as the Python package manager.
- API credentials and secrets must be managed securely using a `.env` file and the `python-dotenv` library.

### Setup Instructions
1. Install `uv`.
2. Clone the repository and navigate to the project root.
3. Sync dependencies: `uv sync`
4. Copy `.env.example` to `.env` and fill in your J-Quants API credentials.
