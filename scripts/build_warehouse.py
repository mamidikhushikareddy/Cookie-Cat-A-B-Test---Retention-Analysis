"""Build a local DuckDB warehouse from the validated Cookie Cats source CSV."""
from pathlib import Path
import sys
import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.cookie_cat import load_and_validate

def main():
    csv_path = ROOT / "data" / "raw" / "cookie_cats.csv"
    if not csv_path.exists():
        raise FileNotFoundError("Run `python run_all.py` first to download the dataset.")
    df = load_and_validate(csv_path)
    db_path = ROOT / "data" / "warehouse" / "cookie_cat.duckdb"
    con = duckdb.connect(str(db_path))
    try:
        con.register("source_df", df)
        con.execute("CREATE OR REPLACE TABLE player_experiment AS SELECT * FROM source_df")
        con.execute("""
            CREATE OR REPLACE VIEW retention_by_gate AS
            SELECT version AS gate_group,
                   COUNT(*) AS players,
                   SUM(CAST(retention_1 AS INTEGER)) AS day1_retained,
                   AVG(CAST(retention_1 AS INTEGER)) AS day1_retention,
                   SUM(CAST(retention_7 AS INTEGER)) AS day7_retained,
                   AVG(CAST(retention_7 AS INTEGER)) AS day7_retention,
                   AVG(sum_gamerounds) AS mean_game_rounds,
                   MEDIAN(sum_gamerounds) AS median_game_rounds
            FROM player_experiment
            GROUP BY version
        """)
        con.execute("""
            CREATE OR REPLACE VIEW experiment_quality AS
            SELECT version AS gate_group, COUNT(*) AS players,
                   COUNT(DISTINCT userid) AS unique_players,
                   COUNT(*) - COUNT(DISTINCT userid) AS duplicate_ids,
                   SUM(CASE WHEN sum_gamerounds < 0 THEN 1 ELSE 0 END) AS negative_rounds
            FROM player_experiment GROUP BY version
        """)
        print(f"Built DuckDB warehouse: {db_path}")
        print(con.execute("SELECT * FROM retention_by_gate ORDER BY gate_group").df().to_string(index=False))
    finally:
        con.close()

if __name__ == "__main__":
    main()
