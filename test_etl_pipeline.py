from src.etl_pipeline import ETLPipeline
import polars as pl
import os

def test_etl_pipeline():
    pipeline = ETLPipeline(processed_data_dir="data/test_processed")

    mock_data = [
        {"Date": "2023-01-04", "Code": "65990", "AdjustmentOpen": 100.0, "AdjustmentHigh": 110.0, "AdjustmentLow": 90.0, "AdjustmentClose": 105.0, "AdjustmentVolume": 1000.0},
        {"Date": "2023-01-05", "Code": "65990", "AdjustmentOpen": 106.0, "AdjustmentHigh": 115.0, "AdjustmentLow": 100.0, "AdjustmentClose": 112.0, "AdjustmentVolume": 1200.0},
        {"Date": "2023-01-06", "Code": "65990", "AdjustmentOpen": 110.0, "AdjustmentHigh": 112.0, "AdjustmentLow": 105.0, "AdjustmentClose": 108.0, "AdjustmentVolume": 800.0},
    ]

    df = pipeline.load_raw_data(mock_data)
    assert len(df) == 3

    processed_df = pipeline.process_daily_quotes(df)
    assert "DayOfWeek" in processed_df.columns
    assert "DailyReturn" in processed_df.columns
    assert "IntradayReturn" in processed_df.columns
    assert "OvernightReturn" in processed_df.columns

    # Intraday return for day 1: (105 - 100) / 100 = 0.05
    assert abs(processed_df.filter(pl.col("Date") == pl.date(2023, 1, 4))["IntradayReturn"][0] - 0.05) < 1e-6

    # Daily return for day 2: (112 - 105) / 105 = 0.0666...
    assert abs(processed_df.filter(pl.col("Date") == pl.date(2023, 1, 5))["DailyReturn"][0] - 0.0666666) < 1e-5

    filepath = pipeline.save_to_parquet(processed_df, "test.parquet")
    assert os.path.exists(filepath)

    loaded_df = pipeline.load_from_parquet("test.parquet")
    assert len(loaded_df) == 3

    print("ETL tests passed.")

test_etl_pipeline()
