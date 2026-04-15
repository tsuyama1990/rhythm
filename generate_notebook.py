import nbformat as nbf

nb = nbf.v4.new_notebook()

cells = [
    nbf.v4.new_markdown_cell("""# 日本株カレンダー・アノマリー分析システム - データ取得・ETL

このノートブックでは、J-Quants APIからのデータ取得と、Polarsを用いたデータの前処理・特徴量生成・Parquet保存（ETLパイプライン）を実行します。"""),

    nbf.v4.new_code_cell("""import os
import sys
import polars as pl
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.abspath('..'))

from src.jquants_client import JQuantsClient
from src.etl_pipeline import ETLPipeline

# 環境変数の読み込み (.envファイル)
load_dotenv('../.env')"""),

    nbf.v4.new_markdown_cell("""## 1. J-Quants API クライアントの初期化"""),

    nbf.v4.new_code_cell("""# クライアントの初期化（環境変数から認証情報を自動読み込み）
try:
    client = JQuantsClient()
    print("APIクライアントの初期化に成功しました。")
except Exception as e:
    print(f"初期化エラー: {e}")"""),

    nbf.v4.new_markdown_cell("""## 2. 銘柄情報の取得と対象銘柄の絞り込み
Freeプラン（直近12週間）を想定し、特定の銘柄（例: エブレン 6599, シグマ光機 7713）に絞って処理を行います。"""),

    nbf.v4.new_code_cell("""# ターゲット銘柄のリスト (5桁コード：末尾に0をつけることが多い)
TARGET_CODES = ["65990", "77130"]

# 全銘柄情報を取得し、ターゲットのみにフィルタリング
# listed_info = client.fetch_listed_info()
# target_info = [info for info in listed_info if info.get("Code") in TARGET_CODES]

# ※ テスト時はAPI負荷軽減のためモックとして情報を作成することも可能
target_info = [{"Code": code} for code in TARGET_CODES]
print(f"対象銘柄数: {len(target_info)}")"""),

    nbf.v4.new_markdown_cell("""## 3. 日足データの取得 (Ingestion)"""),

    nbf.v4.new_code_cell("""all_quotes = []

for code in TARGET_CODES:
    print(f"[{code}] データ取得中...")
    try:
        # Freeプランのため、期間指定なしで直近12週を取得（あるいはfrom/toを指定）
        quotes = client.fetch_daily_quotes(code=code)
        all_quotes.extend(quotes)
        print(f"[{code}] {len(quotes)}件のデータを取得しました。")
    except Exception as e:
         print(f"[{code}] データ取得エラー: {e}")

print(f"合計取得件数: {len(all_quotes)}")"""),

    nbf.v4.new_markdown_cell("""## 4. データの前処理と特徴量生成 (Transformation)"""),

    nbf.v4.new_code_cell("""pipeline = ETLPipeline(raw_data_dir='../data/raw', processed_data_dir='../data/processed')

# rawデータをPolars DataFrameに変換
raw_df = pipeline.load_raw_data(all_quotes)
print("--- Raw DataFrame ---")
print(raw_df.head(3))

# ETL処理の実行
processed_df = pipeline.process_daily_quotes(raw_df)

# 基本的なファンダメンタルズフィルタリング（現在はモック実装）
filtered_df = pipeline.filter_by_fundamentals(processed_df, target_info)

print("\\n--- Processed DataFrame ---")
print(filtered_df.head(5))"""),

    nbf.v4.new_markdown_cell("""## 5. Parquetファイルへの保存"""),

    nbf.v4.new_code_cell("""if not filtered_df.is_empty():
    save_path = pipeline.save_to_parquet(filtered_df, "daily_quotes_target.parquet")
    print(f"処理完了: {save_path} に保存しました。")

    # 読み込みテスト
    test_load_df = pipeline.load_from_parquet("daily_quotes_target.parquet")
    print(f"保存データ件数: {len(test_load_df)}")
else:
    print("保存するデータがありません。")""")
]

nb['cells'] = cells

with open('notebooks/01_data_ingestion.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Notebook generated.")
