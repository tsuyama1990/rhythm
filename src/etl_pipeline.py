import polars as pl
from typing import List, Dict, Optional
import os

class ETLPipeline:
    def __init__(self, raw_data_dir: str = "data/raw", processed_data_dir: str = "data/processed"):
        self.raw_data_dir = raw_data_dir
        self.processed_data_dir = processed_data_dir
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.processed_data_dir, exist_ok=True)

    def load_raw_data(self, data: List[Dict]) -> pl.DataFrame:
        """Convert a list of dictionaries (API response) into a Polars DataFrame."""
        if not data:
            # Return an empty DataFrame with expected schema
            return pl.DataFrame(schema={
                "Date": pl.String,
                "Code": pl.String,
                "Open": pl.Float64,
                "High": pl.Float64,
                "Low": pl.Float64,
                "Close": pl.Float64,
                "Volume": pl.Float64,
                "TurnoverValue": pl.Float64,
                "AdjustmentFactor": pl.Float64,
                "AdjustmentOpen": pl.Float64,
                "AdjustmentHigh": pl.Float64,
                "AdjustmentLow": pl.Float64,
                "AdjustmentClose": pl.Float64,
                "AdjustmentVolume": pl.Float64
            })
        return pl.DataFrame(data)

    def process_daily_quotes(self, df: pl.DataFrame) -> pl.DataFrame:
        """Process daily quotes: type conversion, missing value handling, and feature generation."""
        if df.is_empty():
            return df

        # 1. Type conversion and basic cleaning
        df = df.with_columns([
            pl.col("Date").str.strptime(pl.Date, "%Y-%m-%d"),
            pl.col("Code").cast(pl.String),
            pl.col("AdjustmentOpen").cast(pl.Float32),
            pl.col("AdjustmentHigh").cast(pl.Float32),
            pl.col("AdjustmentLow").cast(pl.Float32),
            pl.col("AdjustmentClose").cast(pl.Float32),
            pl.col("AdjustmentVolume").cast(pl.Float32)
        ])

        # Forward fill for missing prices (e.g. days with zero volume)
        # Note: In a real scenario, you'd sort by Code and Date, then forward fill per Code
        df = df.sort(["Code", "Date"])
        df = df.with_columns([
            pl.col("AdjustmentClose").forward_fill().over("Code").alias("AdjustmentClose"),
            # Open, High, Low should probably just take the filled Close price if they were null,
            # but usually J-Quants provides them. For simplicity, we just forward fill.
            pl.col("AdjustmentOpen").forward_fill().over("Code").alias("AdjustmentOpen"),
            pl.col("AdjustmentHigh").forward_fill().over("Code").alias("AdjustmentHigh"),
            pl.col("AdjustmentLow").forward_fill().over("Code").alias("AdjustmentLow"),
        ])

        # 2. Time-based features
        df = df.with_columns([
            # Day of week: 1 (Monday) to 5 (Friday) in Polars (1 to 7 actually)
            pl.col("Date").dt.weekday().alias("DayOfWeek"),

            # Month start/end flags (simplified based on calendar month, not business days)
            # A more robust business day calculation might require a custom calendar
            (pl.col("Date").dt.day() <= 3).alias("IsEarlyMonth"),
            (pl.col("Date").dt.month() != (pl.col("Date") + pl.duration(days=3)).dt.month()).alias("IsLateMonth")
        ])

        # 3. Return calculations (using shift(1) to avoid look-ahead bias)
        # Daily Return: (Close - PrevClose) / PrevClose
        # Intraday Return: (Close - Open) / Open
        # Overnight Return: (Open - PrevClose) / PrevClose

        df = df.with_columns([
            pl.col("AdjustmentClose").shift(1).over("Code").alias("PrevClose")
        ])

        df = df.with_columns([
            ((pl.col("AdjustmentClose") - pl.col("PrevClose")) / pl.col("PrevClose")).alias("DailyReturn"),
            ((pl.col("AdjustmentClose") - pl.col("AdjustmentOpen")) / pl.col("AdjustmentOpen")).alias("IntradayReturn"),
            ((pl.col("AdjustmentOpen") - pl.col("PrevClose")) / pl.col("PrevClose")).alias("OvernightReturn")
        ])

        return df

    def filter_by_fundamentals(self, df: pl.DataFrame, listed_info: List[Dict] = None) -> pl.DataFrame:
        """Mock function for fundamental filtering."""
        # For phase 1 (Free Plan), we don't have deep fundamentals, so we just return the DF.
        # We can simulate filtering by just keeping specific codes passed in listed_info if needed.
        if listed_info:
            allowed_codes = [info.get("Code") for info in listed_info if info.get("Code")]
            if allowed_codes:
                df = df.filter(pl.col("Code").is_in(allowed_codes))
        return df

    def save_to_parquet(self, df: pl.DataFrame, filename: str) -> str:
        """Save DataFrame to Parquet file."""
        filepath = os.path.join(self.processed_data_dir, filename)
        df.write_parquet(filepath)
        return filepath

    def load_from_parquet(self, filename: str) -> pl.DataFrame:
        """Load DataFrame from Parquet file."""
        filepath = os.path.join(self.processed_data_dir, filename)
        return pl.read_parquet(filepath)
