"""Run every day-1 query against the synthetic data with DuckDB (Postgres-compatible syntax) and save the outputs."""
import pathlib
import duckdb

HERE = pathlib.Path(__file__).parent
con = duckdb.connect()
for p in (HERE / "synthetic").glob("*.parquet"):
    con.execute(f"CREATE VIEW {p.stem} AS SELECT * FROM read_parquet('{p}')")
(HERE / "sample_output").mkdir(exist_ok=True)
for q in sorted(HERE.glob("0*.sql")):
    sql = q.read_text().replace(":'as_of'", "'2026-10-25'")
    df = con.execute(sql).df()
    df.to_csv(HERE / "sample_output" / f"{q.stem}.csv", index=False)
    print(f"\n== {q.stem} ({len(df)} rows, SYNTHETIC)\n{df.head(6).to_string(index=False)}")
