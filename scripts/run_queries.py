"""Run sql/*.sql against the Instacart CSVs with DuckDB and save each result to results/<name>.csv."""
import pathlib
import sys
import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data" / "instacart").resolve()

con = duckdb.connect(str(ROOT / "data" / "instacart.duckdb"))
con.execute((ROOT / "sql" / "00_setup.sql").read_text().replace("{DATA}", str(DATA)))
(ROOT / "results").mkdir(exist_ok=True)

for path in sorted((ROOT / "sql").glob("0[1-9]_*.sql")):
    df = con.execute(path.read_text()).df()
    df.to_csv(ROOT / "results" / f"{path.stem}.csv", index=False)
    print(f"\n== {path.stem}\n{df.head(20).to_string(index=False)}")
